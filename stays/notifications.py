"""Booking messages shared by demo and verified Paystack flows.

Console email is the safe default. Configure a delivery provider separately.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

GUEST_MESSAGES = {
    'PENDING': ('Complete your booking', 'We have received your booking request. Your apartment is temporarily held while you complete payment. Your stay is confirmed only after payment is verified.'),
    'REVIEW': ('Your dates are being reviewed', 'We have received your request. These dates need an availability review, so your stay is not yet confirmed. No payment has been taken. Our team will contact you about availability or alternative dates.'),
    'CONFIRMED': ('Your booking is confirmed', 'Your payment has been verified and your apartment is reserved. We look forward to welcoming you to Trake Apartments by Orleans.'),
    'PAID_REVIEW': ('Payment received: availability review needed', 'Your payment has been received, but we still need to resolve availability. Your stay is not yet confirmed. Our team will contact you about the next steps.'),
    'DECLINED': ('Update on your booking request', 'We are unable to accept your requested dates. No payment has been taken for this request. Please contact our team to discuss another stay.'),
}

def queue_emails(booking, message, *, demo=False):
    """Send only after the booking transaction commits; alerts remain if mail fails."""
    subject, explanation = GUEST_MESSAGES[booking.status]
    context = {'booking': booking, 'explanation': explanation, 'message': message, 'demo': demo}
    guest_body = render_to_string('emails/guest.txt', context)
    owner_body = render_to_string('emails/owner.txt', context)
    prefix = '[DEMO] ' if demo else ''
    def deliver():
        deliveries = [(prefix + subject + ' · ' + booking.reference, guest_body, [booking.email])]
        if settings.BUSINESS_ALERT_EMAILS:
            deliveries.append((prefix + 'Trake: ' + message + ' · ' + booking.reference, owner_body, settings.BUSINESS_ALERT_EMAILS))
        for title, body, recipients in deliveries:
            try:
                send_mail(title, body, settings.DEFAULT_FROM_EMAIL, recipients)
            except Exception:
                logger.exception('Booking email failed; dashboard notification retained')
    transaction.on_commit(deliver)
