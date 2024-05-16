from django.core.management.base import BaseCommand

from apps.finance.models import ProgramResult


class Command(BaseCommand):
    def handle(self, *args, **options):
        accruals_settings = ProgramResult.objects.first()
        if accruals_settings:
            accruals_settings.save()
