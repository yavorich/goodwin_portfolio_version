from django.db.models import Model, ForeignKey, CASCADE, DateField, DecimalField

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
