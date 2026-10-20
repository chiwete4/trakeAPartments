"""Provisional apartment catalogue and photographed spaces, October 2026."""
APARTMENTS = [
    dict(name='1 Bed Classic', slug='one-bedroom-classic', bedrooms=1, max_guests=2, nightly_rate=90000,
         description='A comfortable one-bedroom space with a furnished lounge and an open kitchenette. An easy place to settle into your own routine.',
         photos=[('classic-01','Living area and kitchenette'),('classic-02','Bedroom'),('classic-03','Bathroom'),('classic-04','Kitchenette and appliances')]),
    dict(name='1 Bed Large', slug='one-bedroom-large', bedrooms=1, max_guests=2, nightly_rate=105000,
         description='A one-bedroom apartment with a separate lounge, a welcoming bedroom and a private bathroom. A little more space for your stay.',
         photos=[('large-01','Living area'),('large-02','Bedroom'),('large-03','Bathroom')]),
    dict(name='1 Bed Grand', slug='one-bedroom-grand', bedrooms=1, max_guests=2, nightly_rate=120000,
         description='A generous one-bedroom apartment with a curved lounge sofa, a kitchen and dining corner, and a separate bedroom to unwind in.',
         photos=[('grand-01','Living area'),('grand-02','Lounge, another angle'),('grand-03','Kitchen and dining corner'),('grand-04','Bedroom, another angle'),('grand-05','Bedroom'),('grand-06','Bathroom')]),
    dict(name='2 Bed Apartment', slug='two-bedroom-apartment', bedrooms=2, max_guests=4, nightly_rate=175000,
         description='Two bedrooms with a shared lounge and open kitchen. A relaxed space for families, friends and a longer change of scene.',
         photos=[('two-bed-02','Lounge and open kitchen'),('two-bed-01','Living area'),('two-bed-03','Living area, another angle'),('two-bed-04','Kitchen and breakfast counter'),('two-bed-05','First bedroom'),('two-bed-06','First bedroom, another angle'),('two-bed-07','Second bedroom'),('two-bed-08','Second bedroom, another angle')]),
]

def defaults(item):
    return {key:value for key,value in item.items() if key not in ['slug','photos']} | {
        'image':f"images/apartments/{item['photos'][0][0]}.webp",
        'gallery':[{'path':f'images/apartments/{key}.webp','alt':f"{item['name']} · {label}"} for key,label in item['photos']],
        'is_active':True,
    }
