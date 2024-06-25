from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta, datetime

from apps.gdw_site.models import FundProfitStats, Program, FundTotalStats


class Command(BaseCommand):
    def handle(self, *args, **options):
        annual_profit_values = ["29.64", "31.02", "32.10"]
        descriptions = [
            "Подходит для закрытия ежемесячных потребностей",
            "Подходит для временного прироста капитала",
            "Подходит для реализации ежегодных целей",
        ]
        for i, program in enumerate(Program.objects.all()):
            program.annual_profit = Decimal(annual_profit_values[i])
            program.description = descriptions[i]
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

        total = 0
        for year in range(2021, 2025):
            for month in FundTotalStats.Month.values:
                total += 1
                FundTotalStats.objects.update_or_create(
                    year=year, month=month, defaults=dict(total=Decimal(total))
                )
