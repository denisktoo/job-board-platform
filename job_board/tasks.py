from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_company_registration_confirmation_email(email, name, location, industry):
    """
    Send booking confirmation email asynchronously.
    """
    subject = f"Welcome {name} to Job Board Platform!"
    message = (
        f"Hello {name},\n\n"
        f"Your company has been successfully registered.\n\n"
        f"Details:\n"
        f"📍 Location: {location}\n"
        f"🏢 Industry: {industry}\n\n"
        f"Thank you for joining us!\n\n"
        f"Best regards,\n"
        f"The Job Board Team"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

    return f"Company Registration email sent to {email}"
