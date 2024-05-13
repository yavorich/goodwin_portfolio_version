from decimal import Decimal
from django.db import models
from django.utils.timezone import now, timedelta


from apps.finance.services import get_wallet_settings_attr
from core.utils import blank_and_null, decimal_usdt


class FrozenItem(models.Model):
    class Status(models.TextChoices):
        INITIAL = "initial", "Ожидает разморозки"
        DONE = "done", "Разморожено"

    wallet = models.ForeignKey(
        "Wallet",
        verbose_name="Кошелёк",
        related_name="frozen_items",
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField("Сумма", **decimal_usdt)
    frost_date = models.DateField("Дата заморозки", auto_now_add=True)
    defrost_date = models.DateField("Срок разморозки", **blank_and_null)
    status = models.CharField("Статус", choices=Status.choices, default=Status.INITIAL)

    class Meta:
        ordering = ["-defrost_date"]
        verbose_name = "Замороженная сумма"
        verbose_name_plural = "Замороженные средства"

    def defrost(self, value: Decimal | None = None):
        if not value or value == self.amount:
            self.status = self.Status.DONE
        else:
            self.amount -= value

        self.save()

    def _set_defrost_date(self):
        if not self.defrost_date:
            defrost_days = get_wallet_settings_attr(self.wallet, "defrost_days")
            self.defrost_date = now().date() + timedelta(days=defrost_days)
