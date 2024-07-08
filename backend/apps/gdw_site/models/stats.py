from django.db.models import (
    Model,
    DateField,
    DecimalField,
    IntegerChoices,
    IntegerField,
    Sum,
)
from django.utils.timezone import datetime
from django.core.validators import MinValueValidator

from core.utils import decimal_pct


class FundDailyStats(Model):
    date = DateField("Дата", unique=True)
    percent = DecimalField("Прибыль (%)", **decimal_pct)

    @property
    def total(self):
        return FundDailyStats.objects.filter(date__lte=self.date).aggregate(
            total=Sum("percent")
        )["total"]

    class Meta:
        verbose_name = "значение"
        verbose_name_plural = "Ежедневная доходность фонда"
        ordering = ["date"]


class FundMonthlyStats(Model):
    class Month(IntegerChoices):
        JAN = 1, "Январь"
        FEB = 2, "Февраль"
        MAR = 3, "Март"
        APR = 4, "Апрель"
        MAY = 5, "Май"
        JUN = 6, "Июнь"
        JUL = 7, "Июль"
        AUG = 8, "Август"
        SEP = 9, "Сентябрь"
        OCT = 10, "Октябрь"
        NOV = 11, "Ноябрь"
        DEC = 12, "Декабрь"

    year = IntegerField("Год", validators=[MinValueValidator(2021)])
    month = IntegerField("Месяц", choices=Month.choices)
    total = DecimalField("Суммарный доход (%)", **decimal_pct)

    @property
    def date(self):
        return datetime(self.year, self.month, 1).strftime("%m.%y")

    class Meta:
        unique_together = ("year", "month")
        ordering = ["year", "month"]
        verbose_name = "значение"
        verbose_name_plural = "Статистика по месяцам (для графика)"
