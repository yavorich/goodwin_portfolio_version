from django.dispatch import receiver
from django.db.models.signals import post_save

from apps.information.models import FrozenItem, Operation
from apps.information.tasks import defrost_funds
from apps.accounts.services import send_email_confirmation


@receiver(post_save, sender=FrozenItem)
def create_defrost_funds_task(sender, instance: FrozenItem, created, **kwargs):
    if created:
        defrost_funds.apply_async(eta=instance.until, args=[instance.pk])


@receiver(post_save, sender=Operation)
def handle_operation(sender, instance: Operation, created, **kwargs):
    if created:
        if not instance.confirmed:
            send_email_confirmation(instance.wallet.user)
        else:
            instance.apply()
