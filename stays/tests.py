from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase,override_settings
from django.utils import timezone
from django.contrib.auth.models import User,Group
from .models import ApartmentType,Unit,Booking,Payment,Alert
from .services import create_booking,prepare_payment,apply_payment,review_booking,BookingError
class BookingTests(TestCase):
    def setUp(self):
        self.category=ApartmentType.objects.create(name='Classic',slug='classic',bedrooms=1,max_guests=2,nightly_rate=90000,description='Test')
        self.unit=Unit.objects.create(name='A1',apartment_type=self.category)
        self.start=timezone.localdate()+timedelta(days=5)
        self.data=dict(apartment_type=self.category,check_in=self.start,check_out=self.start+timedelta(days=2),guests=2,guest_name='Demo Guest',email='guest@example.com',phone='08000000000',notes='')
        self.owner=User.objects.create_user('owner',password='test-password-only')
        self.owner.groups.add(Group.objects.create(name='Owner'))
        self.manager=User.objects.create_user('manager',password='test-password-only')
        self.manager.groups.add(Group.objects.create(name='Manager'))
    def verified_data(self,p):return dict(reference=p.reference,amount=p.amount,currency='NGN',customer={'email':p.booking.email},status='success',domain='test')
    def test_rate_and_hold_and_conflict(self):
        first=create_booking(self.data);second=create_booking(self.data)
        self.assertEqual(first.total,180000);self.assertEqual(first.unit,self.unit)
        self.assertEqual(first.status,'PENDING');self.assertEqual(second.status,'REVIEW')
    def test_adjacent_stays_do_not_clash(self):
        create_booking(self.data)
        self.data['check_in']=self.data['check_out'];self.data['check_out']+=timedelta(days=2)
        self.assertEqual(create_booking(self.data).status,'PENDING')
    def test_success_is_idempotent(self):
        b=create_booking(self.data);p=prepare_payment(b)
        apply_payment(p.reference,self.verified_data(p));count=Alert.objects.count()
        apply_payment(p.reference,self.verified_data(p));b.refresh_from_db()
        self.assertEqual(b.status,'CONFIRMED');self.assertEqual(Alert.objects.count(),count)
    def test_underpayment_rejected(self):
        b=create_booking(self.data);p=prepare_payment(b);data=self.verified_data(p);data['amount']-=100
        with self.assertRaises(BookingError):apply_payment(p.reference,data)
        p.refresh_from_db();self.assertFalse(p.verified)
    def test_fee_pass_through(self):
        b=create_booking(self.data);p=prepare_payment(b);data=self.verified_data(p);data['requested_amount']=p.amount;data['amount']+=10000
        self.assertEqual(apply_payment(p.reference,data).status,'CONFIRMED')
    def test_wrong_email_currency_and_environment_rejected(self):
        b=create_booking(self.data);p=prepare_payment(b)
        for key,value in [('currency','USD'),('domain','live'),('customer',{'email':'other@example.com'})]:
            data=self.verified_data(p);data[key]=value
            with self.assertRaises(BookingError):apply_payment(p.reference,data)
    def test_late_payment_with_reallocated_unit_needs_review(self):
        b=create_booking(self.data);p=prepare_payment(b)
        b.hold_until=timezone.now()-timedelta(minutes=1);b.save()
        second=create_booking(self.data);p2=prepare_payment(second);apply_payment(p2.reference,self.verified_data(p2))
        self.assertEqual(apply_payment(p.reference,self.verified_data(p)).status,'PAID_REVIEW')
    def test_approval_cannot_double_book(self):
        create_booking(self.data);b=create_booking(self.data)
        with self.assertRaises(BookingError):review_booking(b.pk,self.owner,'approve','Trying allocation')
        Unit.objects.create(name='A2',apartment_type=self.category)
        self.assertEqual(review_booking(b.pk,self.owner,'approve','Alternative unit available').status,'PENDING')
    def test_expired_hold_cannot_start_payment(self):
        b=create_booking(self.data);b.hold_until=timezone.now()-timedelta(minutes=1);b.save()
        with self.assertRaises(BookingError):prepare_payment(b)
    def test_public_pages_and_valid_booking(self):
        for path in ['/','/apartments/','/apartments/classic/','/book/','/staff/login/']:
            self.assertEqual(self.client.get(path).status_code,200)
        data={**self.data,'apartment_type':self.category.pk}
        response=self.client.post('/book/',data)
        self.assertEqual(response.status_code,302);self.assertEqual(self.client.get(response.url).status_code,200)
    def test_dashboard_roles(self):
        self.assertEqual(self.client.get('/dashboard/owner/').status_code,302)
        self.client.force_login(self.owner)
        for path in ['/dashboard/owner/','/dashboard/manager/']: self.assertEqual(self.client.get(path).status_code,200)
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get('/dashboard/manager/').status_code,200)
        self.assertNotEqual(self.client.get('/dashboard/owner/').status_code,200)
    def test_post_only_and_webhook_signature(self):
        self.assertEqual(self.client.get('/payments/webhook/').status_code,405)
        with override_settings(PAYSTACK_SECRET_KEY='sk_test_dummy'):
            self.assertEqual(self.client.post('/payments/webhook/',data='{}',content_type='application/json').status_code,400)
    @override_settings(DEMO_PAYMENTS=False)
    def test_demo_disabled(self):
        b=create_booking(self.data)
        self.assertEqual(self.client.post(f'/booking/{b.access_token}/demo/').status_code,403)
    def test_invalid_dates_and_capacity(self):
        self.data['check_out']=self.data['check_in']
        with self.assertRaises(BookingError):create_booking(self.data)
        self.data['check_out']+=timedelta(days=1);self.data['guests']=3
        with self.assertRaises(BookingError):create_booking(self.data)
