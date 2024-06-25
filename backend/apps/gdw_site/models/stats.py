from django.db.models import (
    Model,
    ForeignKey,
    DateField,
    DecimalField,
    IntegerChoices,
    IntegerField,
    CASCADE,
)
from django.utils.timezone import datetime
from django.core.validators import MinValueValidator, MaxValueValidator

from core.utils import decimal_pct

from .program import SiteProgram


class FundProfitStats(Model):
    program = ForeignKey(SiteProgram, on_delete=CASCADE)
    date = DateField()
    percent = DecimalField(**decimal_pct)

    class Meta:
        unique_together = ("program", "date")


class FundTotalStats(Model):
    class Month(IntegerChoices):
        JAN = 1, "Январь"
        MAR = 3, "Март"
        MAY = 5, "Май"
        JUL = 7, "Июль"
        SEP = 9, "Сентябрь"
        NOV = 11, "Ноябрь"

    year = IntegerField(
        "Год", validators=[MinValueValidator(2021), MaxValueValidator(2024)]
    )
    month = IntegerField("Месяц", choices=Month.choices)
    total = DecimalField("Суммарный доход (%)", **decimal_pct)

    @property
    def date(self):
        return datetime(self.year, self.month, 1).strftime("%m.%y")

    class Meta:
        unique_together = ("year", "month")
        ordering = ["year", "month"]
        verbose_name = "значение"
        verbose_name_plural = "Статистика фонда"
