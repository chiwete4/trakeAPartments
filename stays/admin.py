from django.contrib import admin
from .models import ApartmentType,Unit,Booking,Payment,Alert,Decision
admin.site.site_header='Trake administration'
admin.site.register([ApartmentType,Unit])
@admin.register(Booking,Payment,Alert,Decision)
class ReadOnlyRecords(admin.ModelAdmin):
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
