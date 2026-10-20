from django.db import migrations

CATALOGUE = [{'slug': 'one-bedroom-classic',
  'name': '1 Bed Classic',
  'bedrooms': 1,
  'max_guests': 2,
  'nightly_rate': 90000,
  'description': 'A comfortable one-bedroom space with a furnished lounge and '
                 'an open kitchenette. An easy place to settle into your own '
                 'routine.',
  'image': 'images/apartments/classic-01.webp',
  'gallery': [{'path': 'images/apartments/classic-01.webp',
               'alt': '1 Bed Classic · Living area and kitchenette'},
              {'path': 'images/apartments/classic-02.webp',
               'alt': '1 Bed Classic · Bedroom'},
              {'path': 'images/apartments/classic-03.webp',
               'alt': '1 Bed Classic · Bathroom'},
              {'path': 'images/apartments/classic-04.webp', 'alt': '1 Bed Classic · Kitchenette and appliances'}],
  'is_active': True},
 {'slug': 'one-bedroom-large',
  'name': '1 Bed Large',
  'bedrooms': 1,
  'max_guests': 2,
  'nightly_rate': 105000,
  'description': 'A one-bedroom apartment with a separate lounge, a welcoming '
                 'bedroom and a private bathroom. A little more space for your '
                 'stay.',
  'image': 'images/apartments/large-01.webp',
  'gallery': [{'path': 'images/apartments/large-01.webp',
               'alt': '1 Bed Large · Living area'},
              {'path': 'images/apartments/large-02.webp',
               'alt': '1 Bed Large · Bedroom'},
              {'path': 'images/apartments/large-03.webp',
               'alt': '1 Bed Large · Bathroom'}],
  'is_active': True},
 {'slug': 'one-bedroom-grand',
  'name': '1 Bed Grand',
  'bedrooms': 1,
  'max_guests': 2,
  'nightly_rate': 120000,
  'description': 'A generous one-bedroom apartment with a curved lounge sofa, '
                 'a kitchen and dining corner, and a separate bedroom to '
                 'unwind in.',
  'image': 'images/apartments/grand-01.webp',
  'gallery': [{'path': 'images/apartments/grand-01.webp',
               'alt': '1 Bed Grand · Living area'},
              {'path': 'images/apartments/grand-02.webp',
               'alt': '1 Bed Grand · Lounge, another angle'},
              {'path': 'images/apartments/grand-03.webp',
               'alt': '1 Bed Grand · Kitchen and dining corner'},
              {'path': 'images/apartments/grand-04.webp',
               'alt': '1 Bed Grand · Bedroom, another angle'},
              {'path': 'images/apartments/grand-05.webp',
               'alt': '1 Bed Grand · Bedroom'},
              {'path': 'images/apartments/grand-06.webp',
               'alt': '1 Bed Grand · Bathroom'}],
  'is_active': True},
 {'slug': 'two-bedroom-apartment',
  'name': '2 Bed Apartment',
  'bedrooms': 2,
  'max_guests': 4,
  'nightly_rate': 175000,
  'description': 'Two bedrooms with a shared lounge and open kitchen. A '
                 'relaxed space for families, friends and a longer change of '
                 'scene.',
  'image': 'images/apartments/two-bed-02.webp',
  'gallery': [{'path': 'images/apartments/two-bed-02.webp',
               'alt': '2 Bed Apartment · Lounge and open kitchen'},
              {'path': 'images/apartments/two-bed-01.webp',
               'alt': '2 Bed Apartment · Living area'},
              {'path': 'images/apartments/two-bed-03.webp',
               'alt': '2 Bed Apartment · Living area, another angle'},
              {'path': 'images/apartments/two-bed-04.webp',
               'alt': '2 Bed Apartment · Kitchen and breakfast counter'},
              {'path': 'images/apartments/two-bed-05.webp',
               'alt': '2 Bed Apartment · First bedroom'},
              {'path': 'images/apartments/two-bed-06.webp',
               'alt': '2 Bed Apartment · First bedroom, another angle'},
              {'path': 'images/apartments/two-bed-07.webp',
               'alt': '2 Bed Apartment · Second bedroom'},
              {'path': 'images/apartments/two-bed-08.webp',
               'alt': '2 Bed Apartment · Second bedroom, another angle'}],
  'is_active': True}]

def refresh_catalogue(apps, schema_editor):
    Category=apps.get_model('stays','ApartmentType')
    Unit=apps.get_model('stays','Unit')
    for row in CATALOGUE:
        data=dict(row)
        slug=data.pop('slug')
        category,_=Category.objects.update_or_create(slug=slug,defaults=data)
        Unit.objects.get_or_create(name=slug+'-01',defaults={'apartment_type':category})
    # Retain earlier demo categories and their booking history, but stop new sales.
    Category.objects.filter(slug__in=['two-bedroom-classic','two-bedroom-grand']).update(is_active=False)
    for unit in Unit.objects.filter(apartment_type__slug__in=['two-bedroom-classic','two-bedroom-grand']):
        if not unit.booking_set.filter(status__in=['PENDING','CONFIRMED','PAID_REVIEW']).exists():
            unit.active=False
            unit.save(update_fields=['active'])

class Migration(migrations.Migration):
    dependencies=[('stays','0002_apartmenttype_gallery_apartmenttype_is_active')]
    operations=[migrations.RunPython(refresh_catalogue,migrations.RunPython.noop)]
