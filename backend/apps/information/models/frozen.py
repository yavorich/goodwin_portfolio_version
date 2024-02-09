from django.db import models
from django.utils.timezone import now, timedelta

from core.utils import blank_and_null


class FrozenItem(models.Model):
    wallet = models.ForeignKey(
        "Wallet", related_name="frozen_items", on_delete=models.CASCADE
    )
    amount = models.FloatField()
    defrost_date = models.DateField(**blank_and_null)
    done = models.BooleanField(default=False)

    def defrost(self):
        self.wallet.frozen -= self.amount
        self.wallet.free += self.amount
        self.wallet.save()

        self.done = True
        self.save()

    def _set_defrost_date(self):
        if not self.defrost_date:
            self.defrost_date = now().date() + timedelta(days=30)

    def save(self, *args, **kwargs):
        self._set_defrost_date()
        super().save(*args, **kwargs)
