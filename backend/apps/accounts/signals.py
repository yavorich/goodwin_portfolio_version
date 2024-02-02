import os

from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from rest_framework.exceptions import ValidationError

from apps.accounts.models import (
    User,
    TempData,
    PersonalVerification,
    VerificationStatus,
    AddressVerification,
)
from apps.information.models import Wallet


@receiver(post_save, sender=User)
def create_temp_data(sender, instance, created, **kwargs):
    if created:
        TempData.objects.create(user=instance)


@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)


@receiver(pre_save, sender=PersonalVerification)
@receiver(pre_save, sender=AddressVerification)
def delete_verification_attachment(sender, instance, **kwargs):
    if instance.status == VerificationStatus.APPROVED and instance.file:
        file_path = instance.file.path
        os.remove(file_path)
        instance.file = None
    elif (
        instance.status == VerificationStatus.REJECTED and instance.reject_message == ""
    ):
        raise ValidationError("Reject message is required for REJECTED status.")
