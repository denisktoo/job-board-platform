from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CompanyReview, Notification

@receiver(post_save, sender=CompanyReview)
def create_company_review_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            company=instance.company,
            user=instance.user,
            type='review',
            content=f"New review by {instance.user.username}: {instance.comment[:50]}"
        )