import secrets
from django.db import models
from django.db.models import Q, F
from django.contrib.auth.models import User

def generate_reference():
    return 'TRK-' + secrets.token_hex(16).upper()

class ApartmentType(models.Model):
    name=models.CharField(max_length=100)
    slug=models.SlugField(unique=True)
    bedrooms=models.PositiveSmallIntegerField()
    max_guests=models.PositiveSmallIntegerField()
    nightly_rate=models.PositiveIntegerField(help_text='NGN')
    description=models.TextField()
    is_active=models.BooleanField(default=True)
    gallery=models.JSONField(default=list,blank=True)
    image=models.CharField(max_length=200,default='images/apartment.svg')
    class Meta:
        ordering=['nightly_rate']
    def __str__(self): return self.name

class Unit(models.Model):
    apartment_type=models.ForeignKey(ApartmentType,on_delete=models.PROTECT,related_name='units')
    name=models.CharField(max_length=80,unique=True)
    active=models.BooleanField(default=True)
    def __str__(self): return self.name

class Booking(models.Model):
    class Status(models.TextChoices):
        REVIEW='REVIEW','Needs review'
        PENDING='PENDING','Awaiting payment'
        CONFIRMED='CONFIRMED','Confirmed'
        PAID_REVIEW='PAID_REVIEW','Paid · needs review'
        DECLINED='DECLINED','Declined'
    reference=models.CharField(max_length=40,default=generate_reference,unique=True,editable=False)
    access_token=models.CharField(max_length=40,default=generate_reference,unique=True,editable=False)
    apartment_type=models.ForeignKey(ApartmentType,on_delete=models.PROTECT)
    unit=models.ForeignKey(Unit,on_delete=models.PROTECT,null=True,blank=True)
    guest_name=models.CharField(max_length=120)
    email=models.EmailField()
    phone=models.CharField(max_length=30)
    guests=models.PositiveSmallIntegerField(default=1)
    check_in=models.DateField()
    check_out=models.DateField()
    nightly_rate=models.PositiveIntegerField()
    total=models.PositiveBigIntegerField()
    status=models.CharField(max_length=20,choices=Status.choices)
    hold_until=models.DateTimeField(null=True,blank=True)
    notes=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-created_at']
        constraints=[models.CheckConstraint(condition=Q(check_out__gt=F('check_in')),name='positive_stay')]
    @property
    def nights(self): return (self.check_out-self.check_in).days
    def __str__(self): return self.reference

class Payment(models.Model):
    booking=models.OneToOneField(Booking,on_delete=models.PROTECT,related_name='payment')
    reference=models.CharField(max_length=40,default=generate_reference,unique=True)
    amount=models.PositiveBigIntegerField(help_text='kobo')
    verified=models.BooleanField(default=False)
    authorization_url=models.URLField(blank=True)
    provider_id=models.CharField(max_length=100,blank=True)
    verified_at=models.DateTimeField(null=True,blank=True)

class Alert(models.Model):
    booking=models.ForeignKey(Booking,on_delete=models.CASCADE)
    message=models.CharField(max_length=240)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']

class Decision(models.Model):
    booking=models.ForeignKey(Booking,on_delete=models.PROTECT)
    actor=models.ForeignKey(User,on_delete=models.PROTECT)
    action=models.CharField(max_length=30)
    reason=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
