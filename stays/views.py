import hashlib,hmac,json
from datetime import timedelta
from urllib.parse import urlparse,quote
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.db.models import Sum,Count
from django.shortcuts import get_object_or_404,redirect,render
from django.http import HttpResponse,JsonResponse,HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import ApartmentType,Booking,Payment,Alert
from .forms import BookingForm
from .services import create_booking,review_booking,prepare_payment,paystack,apply_payment,BookingError

def home(request):
    outdoor=request.GET.get('hero')!='lounge'
    return render(request,'home.html',{
        'apartments':ApartmentType.objects.filter(is_active=True),
        'hero_image':'images/property/compound.webp' if outdoor else 'images/apartments/two-bed-02.webp',
        'hero_alt':'The Trake Apartments by Orleans compound at dusk' if outdoor else 'Two-bedroom apartment lounge and open kitchen at Trake Apartments by Orleans',
    })
def explore(request): return render(request,'explore.html',{'apartments':ApartmentType.objects.filter(is_active=True)})
def detail(request,slug): return render(request,'detail.html',{'apartment':get_object_or_404(ApartmentType,slug=slug,is_active=True)})
def book(request):
    form=BookingForm(request.POST or None,initial={'apartment_type':request.GET.get('apartment'),'check_in':request.GET.get('check_in'),'check_out':request.GET.get('check_out')})
    if request.method=='POST' and form.is_valid():
        try:
            b=create_booking(form.cleaned_data)
            return redirect('summary',token=b.access_token)
        except BookingError as exc: form.add_error(None,str(exc))
    return render(request,'book.html',{'form':form,'apartments':ApartmentType.objects.filter(is_active=True)})
def summary(request,token):
    b=get_object_or_404(Booking,access_token=token)
    return render(request,'summary.html',{'booking':b,'hold_active':b.hold_until and b.hold_until>timezone.now()})
@require_POST
def checkout(request,token):
    b=get_object_or_404(Booking,access_token=token)
    try:
        p=prepare_payment(b)
        if settings.DEMO_PAYMENTS:
            return render(request,'demo_checkout.html',{'booking':b})
        if not p.authorization_url:
            data=paystack('/transaction/initialize',{'email':b.email,'amount':str(p.amount),'currency':'NGN','reference':p.reference,'callback_url':request.build_absolute_uri('/payments/callback/')})
            u=urlparse(data.get('authorization_url',''))
            if data.get('reference')!=p.reference or u.scheme!='https' or not (u.hostname=='paystack.com' or (u.hostname or '').endswith('.paystack.com')): raise BookingError('Invalid checkout response.')
            p.authorization_url=data['authorization_url'];p.save(update_fields=['authorization_url'])
        return redirect(p.authorization_url)
    except BookingError as exc: messages.error(request,str(exc));return redirect('summary',token=token)
@require_POST
def demo_complete(request,token):
    if not settings.DEMO_PAYMENTS: return HttpResponseForbidden()
    b=get_object_or_404(Booking,access_token=token)
    try:
        p=prepare_payment(b)
        apply_payment(p.reference,{'reference':p.reference,'amount':p.amount,'currency':'NGN','customer':{'email':b.email},'status':'success','domain':'demo'},demo=True)
    except BookingError as exc: messages.error(request,str(exc))
    return redirect('summary',token=token)
def callback(request):
    p=get_object_or_404(Payment,reference=request.GET.get('reference',''))
    try: apply_payment(p.reference,paystack('/transaction/verify/'+quote(p.reference,safe='')))
    except BookingError as exc: messages.error(request,str(exc))
    return redirect('summary',token=p.booking.access_token)
@csrf_exempt
@require_POST
def webhook(request):
    if not settings.PAYSTACK_SECRET_KEY: return HttpResponse(status=503)
    expected=hmac.new(settings.PAYSTACK_SECRET_KEY.encode(),request.body,hashlib.sha512).hexdigest()
    if not hmac.compare_digest(expected,request.headers.get('x-paystack-signature','')): return HttpResponse(status=400)
    try:
        event=json.loads(request.body)
        if event.get('event')=='charge.success':
            ref=event['data']['reference']
            if Payment.objects.filter(reference=ref).exists(): apply_payment(ref,paystack('/transaction/verify/'+quote(ref,safe='')))
    except (ValueError,KeyError,TypeError,BookingError): return HttpResponse(status=400)
    return HttpResponse(status=200)
def is_manager(user): return user.is_active and (user.is_superuser or user.groups.filter(name__in=['Owner','Manager']).exists())
def is_owner(user): return user.is_active and (user.is_superuser or user.groups.filter(name='Owner').exists())
@login_required
def dashboard(request):
    if is_owner(request.user): return redirect('owner')
    if is_manager(request.user): return redirect('manager')
    return HttpResponseForbidden('This account has no dashboard access.')
@login_required
@user_passes_test(is_manager)
def manager(request):
    bookings=Booking.objects.select_related('apartment_type','unit').all()
    if request.GET.get('q'): bookings=bookings.filter(guest_name__icontains=request.GET['q'])|bookings.filter(reference__icontains=request.GET['q'])|bookings.filter(email__icontains=request.GET['q'])
    if request.GET.get('status'): bookings=bookings.filter(status=request.GET['status'])
    return render(request,'manager.html',{'bookings':bookings[:150],'alerts':Alert.objects.select_related('booking')[:8],'review_count':Booking.objects.filter(status__in=['REVIEW','PAID_REVIEW']).count()})
@login_required
@user_passes_test(is_owner)
def owner(request):
    today=timezone.localdate();month=today.replace(day=1)
    confirmed=Booking.objects.filter(status='CONFIRMED')
    paid=Payment.objects.filter(verified=True)
    revenue=paid.filter(verified_at__date__gte=month).aggregate(total=Sum('amount'))['total'] or 0
    from .models import Unit
    occupied=confirmed.filter(check_in__lte=today,check_out__gt=today,unit__active=True,apartment_type__is_active=True).count()
    units=Unit.objects.filter(active=True,apartment_type__is_active=True).count()
    sales=paid.values('booking__apartment_type__name').annotate(amount=Sum('amount'),count=Count('id')).order_by('-amount')
    for row in sales: row['naira']=row['amount']//100
    return render(request,'owner.html',{'revenue':revenue//100,'occupied':occupied,'units':units,'occupancy':round(occupied/units*100) if units else 0,'upcoming':confirmed.filter(check_out__gt=today).order_by('check_in')[:8],'review_count':Booking.objects.filter(status__in=['REVIEW','PAID_REVIEW']).count(),'sales':sales,'alerts':Alert.objects.select_related('booking')[:5]})
@login_required
@user_passes_test(is_manager)
@require_POST
def decision(request,pk):
    try: review_booking(pk,request.user,request.POST.get('action'),request.POST.get('reason',''))
    except BookingError as exc: messages.error(request,str(exc))
    else: messages.success(request,'Decision saved.')
    return redirect('manager')
def health(request): return JsonResponse({'status':'ok'})
