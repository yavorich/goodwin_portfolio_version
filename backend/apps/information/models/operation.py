from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.utils import blank_and_null, decimal_usdt

from .program import Program, UserProgram, UserProgramReplenishment, UserProgramAccrual
from .wallet import Wallet
from .frozen import FrozenItem


class Operation(models.Model):
    class Type(models.TextChoices):
        REPLENISHMENT = "replenishment", "Пополнение"
        WITHDRAWAL = "withdrawal", "Вывод"
        TRANSFER = "transfer", "Перевод"
        PARTNER_BONUS = "partner_bonus", "Доход филиала"
        PROGRAM_START = "program_start", "Запуск программы"
        PROGRAM_CLOSURE = "program_closure", "Закрытие программы"
        PROGRAM_REPLENISHMENT = "program_replenishment", "Пополнение программы"
        PROGRAM_REPLENISHMENT_CANCEL = (
            "program_replenishment_cancel",
            "Отмена пополнения программы",
        )
        DEFROST = "defrost", "Разморозка активов"
        EXTRA_FEE = "extra_fee", "Списание комиссии Extra Fee"
        PROGRAM_ACCRUAL = "program_accrual", "Начисление по программе"

    type = models.CharField(_("Operation type"), choices=Type.choices)
    wallet = models.ForeignKey(
        Wallet, related_name="operations", on_delete=models.CASCADE
    )
    amount = models.DecimalField(**decimal_usdt, default=0.0)
    amount_free = models.DecimalField(**decimal_usdt, default=0.0)
    amount_frozen = models.DecimalField(**decimal_usdt, default=0.0)
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
    frozen_item = models.ForeignKey(
        FrozenItem,
        related_name="operations",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    sender = models.ForeignKey(
        Wallet,
        related_name="sends",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    receiver = models.ForeignKey(
        Wallet,
        related_name="receives",
        on_delete=models.CASCADE,
        **blank_and_null,
    )

    def clean_program(self, value):
        if not value and self.type.startswith("program"):
            raise ValidationError(
                f"'program' field must be set for operation with type '{self.type}"
            )

    def apply(self):
        with transaction.atomic():
            getattr(self, f"_apply_{self.type}")()
            self.done = True
            self.save()

    def _apply_replenishment(self):
        if self.amount:
            self.actions.create(
                type=Action.Type.REPLENISHMENT,
                target=Action.Target.WALLET,
                amount=self.amount,
            )
        if self.amount_free:
            self.actions.create(
                type=Action.Type.TRANSFER_FREE,
                target=Action.Target.WALLET,
                amount=self.amount_free,
            )
        if self.amount_frozen:
            self.actions.create(
                type=Action.Type.TRANSFER_FROZEN,
                target=Action.Target.WALLET,
                amount=self.amount_frozen,
            )

    def _apply_withdrawal(self):
        self.actions.create(
            type=Action.Type.WITHDRAWAL,
            target=Action.Target.WALLET,
            amount=-self.amount,
        )  # TODO: add accept/reject ?

    def _apply_partner_bonus(self):
        self.actions.create(
            type=Action.Type.LOYALTY_PROGRAM,
            target=Action.Target.WALLET,
            amount=self.amount,
        )

    def _apply_program_start(self):
        self.user_program = UserProgram.objects.create(
            wallet=self.wallet,
            program=self.program,
        )
        self._from_wallet_to_program()

    def _apply_program_closure(self):
        self._from_program_to_wallet(frozen=True)
        if self.user_program.funds == 0:
            self.user_program.close(force=True)

    def _apply_program_replenishment(self):
        self._from_wallet()
        self.user_program.replenishments.create(
            amount=self.amount_free + self.amount_frozen, operation=self
        )

    def _apply_program_replenishment_cancel(self):
        self.user_program = self.replenishment.program
        self.save()
        self.replenishment.cancel(self.amount)
        self._to_wallet(frozen=True)

    def _apply_defrost(self):
        self._to_wallet(frozen=False)
        if self.frozen_item:
            self.frozen_item.defrost()
        else:
            self.wallet.update_balance(frozen=-self.amount)
            Operation.objects.create(
                type=Operation.Type.EXTRA_FEE,
                wallet=self.wallet,
                amount=0.1 * self.amount,
                confirmed=True,
            )

    def _apply_extra_fee(self):
        self.actions.create(
            type=Action.Type.SYSTEM_MESSAGE,
            target=Action.Target.WALLET,
            amount=-self.amount,
        )

    def _apply_program_accrual(self):
        withdrawal_type = self.user_program.program.withdrawal_type
        target = Action.Target.USER_PROGRAM
        if self.amount >= 0:
            action_type = Action.Type.PROFIT_ACCRUAL
            if withdrawal_type == Program.WithdrawalType.DAILY:
                target = Action.Target.WALLET
        else:
            action_type = Action.Type.LOSS_CHARGEOFF

        self.actions.create(type=action_type, amount=self.amount, target=target)

    def _from_wallet(self):
        if self.amount_free:
            self.actions.create(
                type=Action.Type.TRANSFER_FREE,
                target=Action.Target.WALLET,
                amount=-self.amount_free,
            )
        if self.amount_frozen:
            self.actions.create(
                type=Action.Type.TRANSFER_FROZEN,
                target=Action.Target.WALLET,
                amount=-self.amount_frozen,
            )

    def _to_wallet(self, frozen: bool):
        if frozen:
            _type = Action.Type.TRANSFER_FROZEN
        else:
            _type = Action.Type.TRANSFER_FREE

        self.actions.create(
            type=_type,
            target=Action.Target.WALLET,
            amount=self.amount,
        )

    def _to_program(self):
        self.actions.create(
            type=Action.Type.TRANSFER_BETWEEN,
            target=Action.Target.USER_PROGRAM,
            amount=self.amount_free + self.amount_frozen,
        )
        if self.type == self.Type.PROGRAM_REPLENISHMENT:
            self.replenishment.done()

    def _from_wallet_to_program(self):
        self._from_wallet()
        self._to_program()

    def _from_program_to_wallet(self, frozen: bool):
        self._to_wallet(frozen)
        self.actions.create(
            type=Action.Type.TRANSFER_BETWEEN,
            target=Action.Target.USER_PROGRAM,
            amount=-self.amount,
        )


class Action(models.Model):
    class Type(models.TextChoices):
        TRANSFER_FREE = "transfer_free", 'Перевод в раздел "Доступно"'
        TRANSFER_FROZEN = "transfer_frozen", 'Перевод в раздел "Заморожено"'
        TRANSFER_BETWEEN = "transfer_between", "Перевод между счетами"
        WITHDRAWAL = "withdrawal", "Вывод"
        REPLENISHMENT = "replenishment", "Пополнение"
        PROFIT_ACCRUAL = "profit_accrual", "Начисление прибыли"
        LOSS_CHARGEOFF = "loss_chargeoff", "Фиксация убытка"
        LOYALTY_PROGRAM = "loyalty_program", "Программа лояльности"
        SYSTEM_MESSAGE = "system_message", "Системное сообщение"

    class Target(models.TextChoices):
        WALLET = "wallet"
        USER_PROGRAM = "user_program"

    type = models.CharField(choices=Type.choices)
    name = models.CharField(max_length=127, **blank_and_null)
    target = models.CharField(choices=Target.choices)
    operation = models.ForeignKey(
        Operation, related_name="actions", on_delete=models.CASCADE
    )
    target_name = models.CharField(max_length=127, **blank_and_null)
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(**decimal_usdt)

    def apply(self):
        if self.target == self.Target.WALLET:
            if self.type == self.Type.TRANSFER_FROZEN:
                self.operation.wallet.update_balance(frozen=self.amount)
            else:
                self.operation.wallet.update_balance(free=self.amount)
        elif self.target == self.Target.USER_PROGRAM:
            self.operation.user_program.update_balance(amount=self.amount)

    def _get_name(self):
        if self.operation.type == Operation.Type.REPLENISHMENT:
            if not self.operation.sender:
                return "Deposit"
            return f"Receipt from ID{self.operation.sender.user.id}"

        if self.operation.type == Operation.Type.WITHDRAWAL:
            return "Withdrawal request accepted"

        if self.operation.type == Operation.Type.TRANSFER:
            return f"Transfer to client ID{self.operation.receiver.user.id}"

        if self.operation.type == Operation.Type.PROGRAM_START:
            if self.target == self.Target.USER_PROGRAM:
                return (
                    f"The program {self.operation.user_program.name} "
                    "has been started"
                )
            if self.target == self.Target.WALLET:
                return f"Transfer to program {self.operation.user_program.name}"

        if self.operation.type == Operation.Type.PROGRAM_CLOSURE:
            if self.target == self.Target.USER_PROGRAM:
                message = (
                    f"The program {self.operation.user_program.name} "
                    "has been %sclosed"
                )
                if self.operation.user_program.force_closed:
                    return message % "early "
                if self.operation.user_program.status != UserProgram.Status.FINISHED:
                    return message % "partially"
                return message % ""
            if self.target == self.Target.WALLET:
                return f"Transfer to program {self.operation.user_program.name}"

        if self.operation.type == Operation.Type.PROGRAM_REPLENISHMENT:
            if self.target == self.Target.USER_PROGRAM:
                return (
                    f"The program {self.operation.user_program.name} "
                    "has been replenished"
                )
            if self.target == self.Target.WALLET:
                return f"Transfer to program {self.operation.user_program.name}"

        if self.operation.type == Operation.Type.PROGRAM_REPLENISHMENT_CANCEL:
            canceled = (
                self.operation.replenishment.status
                == UserProgramReplenishment.Status.CANCELED
            )
            return (
                f"The program {self.operation.user_program.name} replenishment "
                f"has been {'partially' if not canceled else ''} canceled"
            )

        if self.operation.type == Operation.Type.PROGRAM_ACCRUAL:
            if self.type == self.Type.PROFIT_ACCRUAL:
                return f"Accrual by program {self.operation.user_program.name}"
            if self.type == self.Type.LOSS_CHARGEOFF:
                return f"Loss by program {self.operation.user_program.name}"

        if self.operation.type == Operation.Type.DEFROST:
            if self.operation.frozen_item:
                frost_date = self.operation.frozen_item.frost_date
                return f"Frozen assets from {frost_date} defrosted"
            return "The defrost request has been completed"

        if self.operation.type == Operation.Type.EXTRA_FEE:
            return "Extra Fee commission write-off"

        if self.operation.type == Operation.Type.PARTNER_BONUS:
            return "Branch income"

    def _get_target_name(self):
        return getattr(self.operation, self.target).name
