from django.db.models import (
    Model,
    ForeignKey,
    CASCADE,
    DateField,
    DecimalField,
    IntegerField,
    IntegerChoices,
)
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.timezone import datetime
from apps.finance.models import Program
from core.utils import decimal_pct


class SiteProgram(Program):
    class Meta:
        proxy = True
        verbose_name_plural = "Программы на GDW-сайте"
        verbose_name = "Программа"


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
