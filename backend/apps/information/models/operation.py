from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.utils import blank_and_null

from .program import Program, UserProgram, UserProgramReplenishment, UserProgramAccrual
from .wallet import Wallet


class Operation(models.Model):
    class Type(models.TextChoices):
        REPLENISHMENT = "replenishment"
        WITHDRAWAL = "withdrawal"
        PROFIT_BONUS = "profit_bonus"
        PARTNER_BONUS = "partner_bonus"
        PROGRAM_START = "program_start"
        PROGRAM_EARLY_CLOSURE = "program_early_closure"
        PROGRAM_REPLENISHMENT = "program_replenishment"
        PROGRAM_REPLENISHMENT_CANCEL = "program_replenishment_cancel"
        EXTRA_FEE = "extra_fee"
        PROGRAM_ACCRUAL = "program_accrual"

    type = models.CharField(_("Operation type"), choices=Type.choices)
    wallet = models.ForeignKey(
        Wallet, related_name="operations", on_delete=models.CASCADE
    )
    amount = models.FloatField(default=0.0)
    amount_free = models.FloatField(default=0.0)
    amount_frozen = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)
    done = models.BooleanField(default=False)

    program = models.ForeignKey(
        Program,
        related_name="operations",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    user_program = models.ForeignKey(
        UserProgram,
        related_name="operations",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    replenishment = models.ForeignKey(
        UserProgramReplenishment,
        related_name="operations",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    accrual = models.ForeignKey(
        UserProgramAccrual,
        related_name="operations",
        on_delete=models.CASCADE,
        **blank_and_null,
    )

    def clean_program(self, value):
        if not value and self.type.startswith("program"):
            raise ValidationError(
                f"'program' field must be set for operation with type '{self.type}"
            )

    def save(self, *args, **kwargs):
        if self.type not in [
            self.Type.WITHDRAWAL,
            self.Type.PROGRAM_EARLY_CLOSURE,
            self.Type.PROGRAM_REPLENISHMENT_CANCEL,
        ]:
            self.confirmed = True
        return super().save(*args, **kwargs)

    def apply(self):
        with transaction.atomic():
            getattr(self, f"_apply_{self.type}")()
            self.done = True
            self.save()

    def _apply_replenishment(self):
        self.wallet.update_balance(free=self.amount)

    def _apply_withdrawal(self):
        self.wallet.update_balance(free=-self.amount)

    def _apply_profit_bonus(self):
        self.wallet.update_balance(free=self.amount)

    def _apply_partner_bonus(self):
        self.wallet.update_balance(free=self.amount)

    def _apply_program_start(self):
        self.user_program = UserProgram.objects.create(
            wallet=self.wallet,
            program=self.program,
        )
        self._transfer_wallet_to_program()

    def _apply_program_early_closure(self):
        self._transfer_program_to_wallet(freeze=True)
        if self.user_program.funds == 0:
            self.user_program.close(force=True)

    def _apply_program_replenishment(self):
        self.wallet.update_balance(free=-self.amount_free, frozen=-self.amount_frozen)
        self.user_program.replenishments.create(
            amount=self.amount_free + self.amount_frozen
        )

    def _apply_program_replenishment_cancel(self):
        self.replenishment.cancel(self.amount)
        if self.replenishment.status == UserProgramReplenishment.Status.CANCELED:
            self.amount = self.replenishment.amount
            self.save()

    def _apply_extra_fee(self):
        self.wallet.update_balance(
            free=self.amount_frozen - self.amount_free,
            frozen=-self.amount_frozen,
        )

    def _apply_program_accrual(self):
        # начисление в актив программы
        self.accrual.apply()

        # начисление в кошелек
        withdrawal_type = self.user_program.program.withdrawal_type
        if withdrawal_type == Program.WithdrawalType.DAILY:
            self._transfer_program_to_wallet(freeze=False)

    def _transfer_wallet_to_program(self):
        self.wallet.update_balance(free=-self.amount_free, frozen=-self.amount_frozen)
        self.user_program.update_balance(amount=self.amount_free + self.amount_frozen)

    def _transfer_program_to_wallet(self, freeze: bool):
        if freeze:
            self.wallet.update_balance(frozen=self.amount)
        else:
            self.wallet.update_balance(free=self.amount)
        self.user_program.update_balance(amount=-self.amount)
