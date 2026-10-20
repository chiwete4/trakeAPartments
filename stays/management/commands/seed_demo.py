import os
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth.models import Group,User
from stays.models import ApartmentType,Unit
class Command(BaseCommand):
    help='Create placeholder catalogue and optional owner; never overwrites existing prices/passwords.'
    def handle(self,*args,**kwargs):
        from stays.catalogue import APARTMENTS,defaults
        for item in APARTMENTS:
            category,_=ApartmentType.objects.get_or_create(slug=item['slug'],defaults=defaults(item))
            Unit.objects.get_or_create(name=item['slug']+'-01',defaults={'apartment_type':category})
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
