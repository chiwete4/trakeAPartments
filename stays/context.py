from django.conf import settings
def brand(request):
    return {'demo_payments':settings.DEMO_PAYMENTS,'paystack_ready':bool(settings.PAYSTACK_SECRET_KEY)}
