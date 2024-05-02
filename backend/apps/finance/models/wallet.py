from decimal import Decimal
from django.db import models

from apps.accounts.models import User
from core.utils import decimal_usdt, blank_and_null, decimal_pct

from .frozen import FrozenItem


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

    @property
    def balance(self):
        return self.free + self.frozen

    def update_balance(
        self,
        free: Decimal = Decimal("0.0"),
        frozen: Decimal = Decimal("0.0"),
        item: FrozenItem | None = None,
    ):
        self.free += free
        self.frozen += frozen
        self.save()
        self.update_frozen(frozen, item)

    def update_frozen(self, frozen: Decimal, item: FrozenItem | None = None):
        if item:
            return item.defrost()

        if frozen > 0:
            return self.frozen_items.create(amount=frozen)

        if frozen < 0:
            for item in self.frozen_items.all():
                value = min(abs(frozen), item.amount)
                item.defrost(value)
                frozen += value
                if frozen == 0:
                    return


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


class WalletSettings(models.Model):
    wallet = models.OneToOneField(
        Wallet,
        verbose_name="Настройки",
        related_name="settings",
        on_delete=models.CASCADE,
        **blank_and_null,
        unique=True,
    )
    defrost_days = models.PositiveIntegerField(
        "Время разморозки Базовых Активов (дней)", **blank_and_null
    )
    commission_on_replenish = models.DecimalField(
        "Комиссия за пополнение, %", **decimal_pct, **blank_and_null
    )
    commission_on_withdraw = models.DecimalField(
        "Комиссия за вывод, %", **decimal_pct, **blank_and_null
    )
    success_fee = models.DecimalField("Success fee, %", **decimal_pct, **blank_and_null)
    management_fee = models.DecimalField(
        "Management fee, %", max_digits=6, decimal_places=4, **blank_and_null
    )
    extra_fee = models.DecimalField("Extra fee, %", **decimal_pct, **blank_and_null)
    commission_on_transfer = models.DecimalField(
        "Комиссия за внутренний перевод, %", **decimal_pct, **blank_and_null
    )

    class Meta:
        verbose_name = "настройки"
        verbose_name_plural = "Общие настройки"

    def __str__(self) -> str:
        return ""
