from django.db import models

from apps.accounts.models import User


class Wallet(models.Model):
    user = models.OneToOneField(
        User, related_name="wallet", primary_key=True, on_delete=models.CASCADE
    )
    free = models.FloatField(default=0.0)
    frozen = models.FloatField(default=0.0)

    def update_balance(self, free: float = 0.0, frozen: float = 0.0):
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
                item.amount -= value
                item.save()
                frozen += value
                if frozen == 0:
                    break


class WalletHistory(models.Model):
    user = models.ForeignKey(
        User, related_name="wallet_history", on_delete=models.CASCADE
    )
    free = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        verbose_name="Доступно",
    )
    frozen = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, verbose_name="Заморожено"
    )
    deposits = models.DecimalField(
        max_digits=10,
        decimal_places=2,
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
