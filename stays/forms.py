from django import forms
from django.utils import timezone
from .models import ApartmentType
class BookingForm(forms.Form):
    apartment_type=forms.ModelChoiceField(queryset=ApartmentType.objects.all(),label='Apartment')
    check_in=forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    check_out=forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    guests=forms.IntegerField(min_value=1,max_value=8,initial=1)
    guest_name=forms.CharField(max_length=120,label='Full name')
    email=forms.EmailField()
    phone=forms.CharField(max_length=30)
    notes=forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':3}),label='Anything we should know?')
    def clean(self):
        data=super().clean()
        start,end=data.get('check_in'),data.get('check_out')
        if start and start<timezone.localdate(): self.add_error('check_in','Choose today or a future date.')
        if start and end and end<=start: self.add_error('check_out','Departure must be after arrival.')
        category=data.get('apartment_type')
        if category and data.get('guests',0)>category.max_guests: self.add_error('guests','Too many guests for this apartment.')
        return data
