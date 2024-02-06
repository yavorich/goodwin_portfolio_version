from django.db import models
from django.utils.timezone import now, timedelta


class FrozenItem(models.Model):
    wallet = models.ForeignKey(
        "Wallet", related_name="frozen_items", on_delete=models.CASCADE
    )
    amount = models.FloatField()
    defrost_date = models.DateField(default=now().date() + timedelta(days=30))
    done = models.BooleanField(default=False)

    def defrost(self):
        self.wallet.frozen -= self.amount
        self.wallet.free += self.amount
        self.wallet.save()

        self.done = True
        self.save()
