from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_company_registration_confirmation_email(email, name, location, industry):
    """
    Send company registration email asynchronously.
    """
    subject = f"Welcome {name} to Job Board Platform!"
    message = (
        f"Hello {name},\n\n"
        f"Your company has been successfully registered.\n\n"
        f"Details:\n"
        f"Location: {location}\n"
        f"Industry: {industry}\n\n"
        f"Thank you for joining us!\n\n"
        f"Best regards,\n"
        f"The Job Board Team"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

    return f"Company Registration email sent to {email}"

@shared_task
def send_job_registration_confirmation_email(email, name, title, type, created_at, deadline):
    """
    Send job registration email asynchronously.
    """
    subject = f"{title} Job Registration was successful!"
    message = (
        f"Hello {name},\n\n"
        f"{title} job has been successfully registered.\n\n"
        f"Thank you for working with us!\n\n"
        f"Best regards,\n"
        f"The Job Board Team"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

    return f"Company Job Registration email sent to {email}"

@shared_task
def send_job_application_confirmation_email(email, applicant, title, name, status, applied_at):
    """
    Send job submission email asynchronously.
    """
    subject = f"Thank You for Applying {applicant} – We've Received Your Application!"
    message = (
        f"Hello {applicant},\n\n"
        f"Thank you for applying for the {title} position at {name} company.\n\n"
        f"Details:\n"
        f"Status: {status}\n"
        f"Date: {applied_at}\n\n"
        f"Thanks again, and we wish you the very best in your job search!\n\n"
        f"Best regards,\n"
        f"The Job Board Team"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

    return f"Job application details sent to {email}"
