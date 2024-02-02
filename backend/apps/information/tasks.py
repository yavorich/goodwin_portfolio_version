from celery import shared_task

from apps.information.models import FrozenItem


@shared_task
def defrost_funds(pk):
    try:
        item = FrozenItem.objects.get(pk=pk)
    except FrozenItem.DoesNotExist:
        return
    item.defrost()
