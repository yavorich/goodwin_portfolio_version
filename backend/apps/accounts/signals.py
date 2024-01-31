from django.dispatch import receiver
from django.db.models.signals import post_save

from apps.accounts.models import User, TempData
from apps.information.models import Wallet


@receiver(post_save, sender=User)
def create_temp_data(sender, instance, created, **kwargs):
    if created:
        TempData.objects.create(user=instance)


@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
