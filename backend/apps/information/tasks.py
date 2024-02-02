from celery import shared_task
from django.db import transaction

from apps.information.models import FrozenItem


@shared_task
def defrost_funds(pk):
    with transaction.atomic():
        try:
            item = FrozenItem.objects.get(pk=pk)
        except FrozenItem.DoesNotExist:
            return
        item.defrost()
