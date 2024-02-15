from decimal import Decimal
from django.db import models

from apps.accounts.models import User
from core.utils import decimal_usdt


class Wallet(models.Model):
    user = models.OneToOneField(
        User,
        verbose_name="Пользователь",
        related_name="wallet",
        primary_key=True,
        on_delete=models.CASCADE,
    )
    free = models.DecimalField("Доступно", **decimal_usdt, default=Decimal("0.0"))
    frozen = models.DecimalField("Заморожено", **decimal_usdt, default=Decimal("0.0"))

    class Meta:
        verbose_name = "Кошелёк"
        verbose_name_plural = "Кошельки"

    def __str__(self) -> str:
        return f"Кошелёк пользователя ID{self.user.pk}"

    @property
    def name(self):
        return "Wallet GDW"

    def update_balance(
        self, free: Decimal = Decimal("0.0"), frozen: Decimal = Decimal("0.0")
    ):
        self.free += free
        self.frozen += frozen
        self.save()
        self.update_frozen(frozen)

    def update_frozen(self, frozen):
        if frozen > 0:
            self.frozen_items.create(amount=frozen)

        elif frozen < 0:
            for item in self.frozen_items.all():
                value = min(abs(frozen), item.amount)
                item.defrost(value)
                frozen += value
                if frozen == 0:
                    break


class WalletHistory(models.Model):
    user = models.ForeignKey(
        User, related_name="wallet_history", on_delete=models.CASCADE
    )
    free = models.DecimalField(
        **decimal_usdt,
        default=0.0,
        verbose_name="Доступно",
    )
    frozen = models.DecimalField(**decimal_usdt, default=0.0, verbose_name="Заморожено")
    deposits = models.DecimalField(
        **decimal_usdt,
        default=0.0,
        verbose_name="Сумма базовых активов всех незакрытых программ",
    )
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        unique_together = ("user", "created_at")
        verbose_name = "История кошелька"
        verbose_name_plural = "Истории кошельков"

    def __str__(self):
        return f"{self.user}"
