from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from core.utils import blank_and_null

from .program import UserProgram


class Operation(models.Model):
    class Type(models.TextChoices):
        REPLENISHMENT = "replenishment"
        WITHDRAWAL = "withdrawal"
        PROFIT_BONUS = "profit_bonus"
        PARTNER_BONUS = "partner_bonus"
        PROGRAM_START = "program_start"
        PROGRAM_EARLY_CLOSURE = "program_early_closure"
        REINVESTING = "reinvesting"
        REINVESTING_CANCEL = "reinvesting_cancel"
        EXTRA_FEE = "extra_fee"
        PROGRAM_ACCRUAL = "program_accrual"

    type = models.CharField(_("Operation type"), choices=Type.choices)
    user = models.ForeignKey(
        User, related_name="operations", on_delete=models.CASCADE
    )
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    program = models.ForeignKey(
        UserProgram,
        related_name="operations",
        on_delete=models.CASCADE,
        **blank_and_null
    )
