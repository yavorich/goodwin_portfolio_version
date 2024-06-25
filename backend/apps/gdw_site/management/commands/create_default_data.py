import csv
import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.timezone import datetime
from django.db.models import Sum

from config.settings import BASE_DIR

from apps.gdw_site.models import (
    FundDailyStats,
    SiteProgram,
    FundMonthlyStats,
    SiteAnswer,
    SiteContact,
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        annual_profit_values = ["29.64", "31.02", "32.10"]
        descriptions = [
            "Подходит для закрытия ежемесячных потребностей",
            "Подходит для временного прироста капитала",
            "Подходит для реализации ежегодных целей",
        ]
        for i, program in enumerate(SiteProgram.objects.all()):
            program.annual_profit = Decimal(annual_profit_values[i])
            program.description = descriptions[i]
            program.save()

        FundDailyStats.objects.all().delete()
        FundMonthlyStats.objects.all().delete()

        fieldnames = ("weekday", "date", "percent")
        filepath = os.path.join(BASE_DIR, "apps/gdw_site/src/profits.csv")

        with open(filepath, "r") as f:
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                date = datetime.strptime(row["date"], "%d.%m.%y").date()
                if row["percent"]:
                    percent = Decimal(row["percent"].replace(",", ".").strip("%"))
                else:
                    percent = Decimal("0.00")
                FundDailyStats.objects.create(date=date, percent=percent)

        dates = FundDailyStats.objects.values_list("date", flat=True)
        start_year, end_year = [dates[i].year for i in [0, len(dates)-1]]

        for year in range(start_year, end_year + 1):
            start_month = 1 if year != start_year else dates[0].month
            end_month = 12 if year != end_year else dates[len(dates)-1].month

            for month in range(start_month, end_month + 1):
                next_month = month + 1 if month != 12 else 1
                next_month_first_day = datetime(year + (month == 12), next_month, 1)
                total = FundDailyStats.objects.filter(
                    date__lt=next_month_first_day
                ).aggregate(total=Sum("percent"))["total"] or Decimal("0.0")
                FundMonthlyStats.objects.create(year=year, month=month, total=total)

        SiteAnswer.objects.all().delete()
        for i in range(1, 6):
            SiteAnswer.objects.create(
                title=dict(ru=f"Вопрос {i}", en=f"Question {i}", cn=f"問題 {1}"),
                text=dict(
                    ru="Ответ на вопрос",
                    en="Answer to the question",
                    cn="回答問題",
                ),
            )

        SiteContact.objects.all().delete()
        SiteContact.objects.create(
            address=(
                "RM4, 16/7, HO KING COMM CTR, 2-16 FAYUEN ST, "
                "MONGKOK KOWLOON, HONG KONG"
            ),
            certificate="No. 74497617-000-10-22-4",
            email="goodwin.plc@gmail.com",
            latitude=22.3158422,
            longitude=114.1715726,
        )
