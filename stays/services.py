"""Trake-specific booking allocation; payment checks adapted from Five Homes."""
import json, logging
from datetime import timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, quote
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.core.mail import send_mail
from django.utils import timezone
from .models import ApartmentType, Unit, Booking, Payment, Alert, Decision
logger=logging.getLogger(__name__)
class BookingError(ValueError): pass

def alert(booking,message):
    Alert.objects.create(booking=booking,message=message)
    def email_alert():
        if settings.BUSINESS_ALERT_EMAILS:
            try:
                send_mail('Trake: '+message, f'{booking.reference}\n{booking.guest_name}\n{booking.check_in} to {booking.check_out}\n{message}',settings.DEFAULT_FROM_EMAIL,settings.BUSINESS_ALERT_EMAILS)
            except Exception:
                logger.exception('Business email failed; dashboard alert retained')
    transaction.on_commit(email_alert)

def available_unit(apartment_type,start,end,exclude=None):
    occupied=Booking.objects.filter(check_in__lt=end,check_out__gt=start).filter(Q(status='CONFIRMED')|Q(status='PENDING',hold_until__gt=timezone.now()))
    if exclude: occupied=occupied.exclude(pk=exclude)
    return Unit.objects.filter(apartment_type=apartment_type,active=True).exclude(pk__in=occupied.exclude(unit=None).values('unit_id')).order_by('pk').first()

@transaction.atomic
def create_booking(cleaned):
    category=ApartmentType.objects.select_for_update().get(pk=cleaned['apartment_type'].pk)
    if not category.is_active: raise BookingError('This apartment is no longer available to book.')
    start,end=cleaned['check_in'],cleaned['check_out']
    if start<timezone.localdate() or end<=start: raise BookingError('Please select valid future stay dates.')
    if cleaned['guests']>category.max_guests: raise BookingError('Guest count exceeds this apartment’s capacity.')
    unit=available_unit(category,start,end)
    b=Booking.objects.create(**cleaned,unit=unit,nightly_rate=category.nightly_rate,total=category.nightly_rate*(end-start).days,status='PENDING' if unit else 'REVIEW',hold_until=timezone.now()+timedelta(minutes=20) if unit else None)
    alert(b,'New booking awaiting payment' if unit else 'Availability conflict: booking needs review')
    return b

@transaction.atomic
def review_booking(booking_id,user,action,reason):
    # All allocation paths lock category first to serialize competing reservations.
    category_id=Booking.objects.values_list('apartment_type_id',flat=True).get(pk=booking_id)
    category=ApartmentType.objects.select_for_update().get(pk=category_id)
    b=Booking.objects.select_for_update().get(pk=booking_id)
    if b.status not in ['REVIEW','PAID_REVIEW']: raise BookingError('This booking no longer needs review.')
    if not reason.strip(): raise BookingError('Add a decision note for the audit trail.')
    if action=='approve':
        unit=available_unit(category,b.check_in,b.check_out,exclude=b.pk)
        if not unit: raise BookingError('These dates are still occupied. Resolve the clash or offer the guest different dates first.')
        if b.check_in<timezone.localdate(): raise BookingError('The requested arrival date has passed.')
        b.unit=unit
        b.status='CONFIRMED' if hasattr(b,'payment') and b.payment.verified else 'PENDING'
        b.hold_until=timezone.now()+timedelta(minutes=20) if b.status=='PENDING' else None
    elif action=='decline':
        if hasattr(b,'payment') and b.payment.verified: raise BookingError('This is a paid booking. Resolve the allocation or arrange a refund outside this demo first.')
        b.status='DECLINED'
    else: raise BookingError('Unknown decision.')
    b.save()
    Decision.objects.create(booking=b,actor=user,action=action,reason=reason)
    alert(b,'Booking review: '+b.get_status_display())
    return b

def paystack(path,payload=None):
    key=settings.PAYSTACK_SECRET_KEY
    if not key or not key.startswith('sk_'+settings.PAYSTACK_ENVIRONMENT+'_'): raise BookingError('Paystack test keys have not been configured. No payment has been taken.')
    req=Request('https://api.paystack.co'+path,data=json.dumps(payload).encode() if payload else None,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST' if payload else 'GET')
    try:
        with urlopen(req,timeout=20) as response: result=json.load(response)
    except (URLError,HTTPError,TimeoutError,ValueError) as exc: raise BookingError('Payment provider unavailable. Please retry shortly.') from exc
    if not result.get('status') or not isinstance(result.get('data'),dict): raise BookingError('Payment provider did not accept this request.')
    return result['data']

@transaction.atomic
def prepare_payment(b):
    category=ApartmentType.objects.select_for_update().get(pk=b.apartment_type_id)
    b=Booking.objects.select_for_update().get(pk=b.pk)
    if b.status!='PENDING' or not b.hold_until or b.hold_until<=timezone.now(): raise BookingError('This payment hold has ended or needs staff review. Please create a new booking.')
    unit=available_unit(category,b.check_in,b.check_out,exclude=b.pk)
    if not unit: raise BookingError('Availability changed. Please contact management.')
    b.unit=unit
    b.save(update_fields=['unit'])
    p,_=Payment.objects.get_or_create(booking=b,defaults={'amount':b.total*100})
    return p

@transaction.atomic
def apply_payment(reference,data,*,demo=False):
    p0=Payment.objects.select_related('booking').get(reference=reference)
    category=ApartmentType.objects.select_for_update().get(pk=p0.booking.apartment_type_id)
    b=Booking.objects.select_for_update().get(pk=p0.booking_id)
    p=Payment.objects.select_for_update().get(pk=p0.pk)
    if p.verified: return b
    try:
        charged=int(data.get('amount',-1))
        requested=int(data.get('requested_amount',charged))
    except (ValueError,TypeError): raise BookingError('Invalid provider amount.')
    if not (data.get('status')=='success' and data.get('reference')==p.reference and requested==p.amount and charged>=p.amount and data.get('currency')=='NGN' and (data.get('customer') or {}).get('email','').lower()==b.email.lower() and data.get('domain')==('demo' if demo else settings.PAYSTACK_ENVIRONMENT)):
        raise BookingError('Payment verification did not match this booking.')
    if demo and not settings.DEMO_PAYMENTS: raise BookingError('Demo checkout is disabled.')
    p.verified=True
    p.verified_at=timezone.now()
    p.provider_id=str(data.get('id','demo'))
    p.save()
    unit=available_unit(category,b.check_in,b.check_out,exclude=b.pk)
    if unit and b.status=='PENDING' and b.check_in>=timezone.localdate():
        b.unit=unit
        b.status='CONFIRMED'
    else:
        b.unit=None
        b.status='PAID_REVIEW'
    b.save()
    alert(b,('DEMO · ' if demo else '')+'Payment verified: '+b.get_status_display())
    return b
