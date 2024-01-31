from django.dispatch import receiver
from django.db.models.signals import post_save
from apps.accounts.models import User, TempData


@receiver(post_save, sender=User)
def create_temp_data(sender, instance, created, **kwargs):
    if created:
        TempData.objects.get_or_create(user=instance)
