from django.core.management.base import BaseCommand
from django.utils.timezone import datetime

from apps.finance.models import WithdrawalRequest


class Command(BaseCommand):
    def handle(self, *args, **options):
        for request in WithdrawalRequest.objects.all():
            if request.created_at:
                request.created_at_datetime = datetime(
                    request.created_at.year,
                    request.created_at.month,
                    request.created_at.day,
                    0,
                    0,
                    0,
                ).astimezone(datetime.now().tzinfo)
                request.save()
