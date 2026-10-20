import os
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth.models import Group,User
from stays.models import ApartmentType,Unit
class Command(BaseCommand):
    help='Create placeholder catalogue and optional owner; never overwrites existing prices/passwords.'
    def handle(self,*args,**kwargs):
        for name,slug,beds,rate,desc in [('One Bedroom · Classic','one-bedroom-classic',1,90000,'A calm, thoughtfully arranged one-bedroom apartment. Your own living area, kitchen and space to unwind.'),('One Bedroom · Grand','one-bedroom-grand',1,120000,'More room to settle in. A generous one-bedroom apartment with an expansive living area and a relaxed residential feel.'),('Two Bedroom · Classic','two-bedroom-classic',2,150000,'Two private bedrooms and a shared space to reconnect. An easy choice for families and friends.'),('Two Bedroom · Grand','two-bedroom-grand',2,200000,'Our most spacious stay. Two bedrooms, a generous lounge and room for life to unfold at your pace.')]:
            category,_=ApartmentType.objects.get_or_create(slug=slug,defaults={'name':name,'bedrooms':beds,'max_guests':beds*2,'nightly_rate':rate,'description':desc})
            Unit.objects.get_or_create(name=slug+'-01',defaults={'apartment_type':category})
        for name in ['Owner','Manager']: Group.objects.get_or_create(name=name)
        username=os.getenv('DEMO_OWNER_USERNAME')
        password=os.getenv('DEMO_OWNER_PASSWORD')
        if username and password:
            if len(password)<12: raise CommandError('Use an owner password of at least 12 characters.')
            user,created=User.objects.get_or_create(username=username)
            if created:
                user.set_password(password);user.save()
                user.groups.add(Group.objects.get(name='Owner'))
        self.stdout.write(self.style.SUCCESS('Catalogue ready. One placeholder physical unit per category; update inventory before taking real bookings.'))
