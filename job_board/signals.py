from django.db.models import Q
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Message, MessageHistory, Notification, Profile, User


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        message_sender = instance.sender
        message_receiver = instance.receiver

        if not message_receiver:
            conversation = instance.conversation
            message_receiver = conversation.participants.exclude(
                user_id=message_sender.user_id
            ).first()

        if message_receiver and message_receiver != message_sender:
            Notification.objects.create(
                message=instance,
                receiver=message_receiver,
                type="message",
                notification=f"New message notification from {message_sender.username}",
            )


@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        previous_message = Message.objects.get(pk=instance.pk)
    except Message.DoesNotExist:
        return

    if previous_message.content != instance.content:
        MessageHistory.objects.create(
            message=previous_message,
            old_content=previous_message.content,
        )
        instance.edited = True


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_delete, sender=User)
def cleanup_user_related_data(sender, instance, **kwargs):
    message_ids = list(
        Message.objects.filter(Q(sender=instance) | Q(receiver=instance)).values_list(
            "message_id", flat=True
        )
    )

    if message_ids:
        MessageHistory.objects.filter(message_id__in=message_ids).delete()
        Notification.objects.filter(message_id__in=message_ids).delete()
        Message.objects.filter(message_id__in=message_ids).delete()

    Notification.objects.filter(receiver=instance).delete()
