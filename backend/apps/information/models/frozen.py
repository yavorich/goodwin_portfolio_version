from django.db import models
from django.utils.timezone import now, timedelta

from core.utils import blank_and_null


class FrozenItem(models.Model):
    class Status(models.TextChoices):
        INITIAL = "initial", "Ожидает разморозки"
        DONE = "done", "Разморожено"

    wallet = models.ForeignKey(
        "Wallet", related_name="frozen_items", on_delete=models.CASCADE
    )
    amount = models.FloatField()
    frost_date = models.DateField(auto_now_add=True)
    defrost_date = models.DateField(**blank_and_null)
    status = models.CharField(choices=Status.choices, default=Status.INITIAL)

    class Meta:
        ordering = ["-defrost_date"]

    def defrost(self):
        self.amount = 0
        self.save()

    def _set_defrost_date(self):
        if not self.defrost_date:
            self.defrost_date = now().date() + timedelta(days=30)

    def save(self, *args, **kwargs):
        self._set_defrost_date()
        if self.amount == 0:
            self.status = self.Status.DONE
        super().save(*args, **kwargs)
