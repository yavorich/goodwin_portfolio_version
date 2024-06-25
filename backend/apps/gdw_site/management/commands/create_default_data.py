from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta, datetime

from apps.gdw_site.models import FundProfitStats, Program


class Command(BaseCommand):
    def handle(self, *args, **options):
        annual_profit_values = ["29.64", "31.02", "32.10"]
        for i, program in enumerate(Program.objects.all()):
            program.annual_profit = Decimal(annual_profit_values[i])
            program.save()

        start_date = datetime(2021, 1, 1).date()
        end_date = now().date()

        all_dates = [
            start_date + timedelta(days=x)
            for x in range((end_date - start_date).days + 1)
        ]

        for date in all_dates:
            for program in Program.objects.all():
                daily_profit = program.annual_profit / (365 + (date.year % 4 == 0))
                FundProfitStats.objects.update_or_create(
                    program=program,
                    date=date,
                    defaults=dict(percent=daily_profit),
                )
