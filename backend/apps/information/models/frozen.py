from django.db import models
from django.utils.timezone import now, timedelta


class FrozenItem(models.Model):
    wallet = models.ForeignKey(
        "Wallet", related_name="frozen_items", on_delete=models.CASCADE
    )
    amount = models.FloatField()
    operation = models.ForeignKey(
        "Operation", related_name="frozen_items", on_delete=models.CASCADE
    )
    until = models.DateField(default=now().date() + timedelta(days=30))

    def defrost(self):
        self.wallet.frozen -= self.amount
        self.wallet.free += self.amount
        self.wallet.save()
