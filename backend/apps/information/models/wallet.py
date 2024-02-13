from django.db import models

from apps.accounts.models import User


class Wallet(models.Model):
    user = models.OneToOneField(
        User, related_name="wallet", primary_key=True, on_delete=models.CASCADE
    )
    free = models.FloatField(default=0.0)
    frozen = models.FloatField(default=0.0)

    @property
    def name(self):
        return "Wallet GDW"

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
                item.defrost(value)
                frozen += value
                if frozen == 0:
                    break
