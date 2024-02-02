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
