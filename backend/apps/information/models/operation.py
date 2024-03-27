import random
from decimal import Decimal
from django.db import models, transaction
from django.utils.timezone import now, timedelta

from core.utils import blank_and_null, decimal_usdt

from .program import Program, UserProgram, UserProgramReplenishment
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

    type = models.CharField("Тип операции", choices=Type.choices)
    wallet = models.ForeignKey(
        Wallet,
        verbose_name="Кошелёк",
        related_name="operations",
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField("Сумма", **decimal_usdt, **blank_and_null)
    amount_free = models.DecimalField(
        'Из раздела "Свободно"', **decimal_usdt, **blank_and_null
    )
    amount_frozen = models.DecimalField(
        'Из раздела "Заморожено"', **decimal_usdt, **blank_and_null
    )
    created_at = models.DateTimeField("Дата и время", auto_now_add=True)
    confirmation_code = models.CharField(**blank_and_null)
    confirmation_code_expires_at = models.DateTimeField(**blank_and_null)
    confirmed = models.BooleanField("Подтверждена", default=False)
    done = models.BooleanField("Исполнена", default=False)

    program = models.ForeignKey(
        Program,
        verbose_name="Программа",
        related_name="operations",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    user_program = models.ForeignKey(
        UserProgram,
        verbose_name="Программа пользователя",
        related_name="operations",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    replenishment = models.ForeignKey(
        UserProgramReplenishment,
        verbose_name="Пополнение",
        related_name="operations",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    frozen_item = models.ForeignKey(
        FrozenItem,
        verbose_name="Замороженная сумма",
        related_name="operations",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    sender = models.ForeignKey(
        Wallet,
        verbose_name="Отправитель",
        related_name="sends",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    receiver = models.ForeignKey(
        Wallet,
        verbose_name="Получатель",
        related_name="receives",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    early_closure = models.BooleanField(default=False)
    partial = models.BooleanField(default=False)
    expiration_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Операция"
        verbose_name_plural = "Операции"

    def __str__(self) -> str:
        return Operation.Type(self.type).label

    def set_code(self):
        self.confirmation_code = "".join([str(random.randint(0, 9)) for i in range(6)])
        self.confirmation_code_expires_at = now() + timedelta(minutes=5)

    def apply(self):
        with transaction.atomic():
            done = getattr(self, f"_apply_{self.type}")()
            self.done = done
            self.save()

    def _apply_replenishment(self):
        return False

    def _apply_withdrawal(self):
        return True

    def _apply_transfer(self):
        self._from_wallet()
        Operation.objects.create(
            type=Operation.Type.REPLENISHMENT,
            wallet=self.receiver,
            sender=self.wallet,
            amount_free=(1 - Decimal("0.005")) * self.amount_free,
            amount_frozen=(1 - Decimal("0.005")) * self.amount_frozen,
            confirmed=True,
        )
        return True

    def _apply_partner_bonus(self):
        self.actions.create(
            type=Action.Type.LOYALTY_PROGRAM,
            target=Action.Target.WALLET,
            amount=self.amount,
        )
        return True

    def _apply_program_start(self):
        self.user_program = UserProgram.objects.create(
            wallet=self.wallet,
            program=self.program,
        )
        self._from_wallet_to_program()
        return True

    def _apply_program_closure(self):
        self._from_program_to_wallet(frozen=True)
        if not self.partial:
            self.user_program.close()
            replenishments = self.user_program.replenishments.filter(
                status=UserProgramReplenishment.Status.INITIAL
            )
            for replenishment in replenishments:
                Operation.objects.create(
                    type=Operation.Type.PROGRAM_REPLENISHMENT_CANCEL,
                    wallet=self.wallet,
                    replenishment=replenishment,
                    amount=replenishment.amount,
                    confirmed=True,
                )
        return True

    def _apply_program_replenishment(self):
        self._from_wallet()
        self.user_program.replenishments.create(
            amount=self.amount_free + self.amount_frozen, operation=self
        )
        return False

    def _apply_program_replenishment_cancel(self):
        self.user_program = self.replenishment.program
        self.save()
        if self.partial:
            self.replenishment.decrease(self.amount)
        else:
            self.replenishment.cancel()
        self._to_wallet(frozen=True)
        return True

    def _apply_defrost(self):
        if self.frozen_item:
            self.wallet.update_balance(
                frozen=-self.amount, item=self.frozen_item  # разморозка frozen-item
            )
        else:
            self.wallet.update_balance(frozen=-self.amount)  # разморозка суммы
            Operation.objects.create(
                type=Operation.Type.EXTRA_FEE,
                wallet=self.wallet,
                amount=Decimal("0.1") * self.amount,
                confirmed=True,
            )
        self._to_wallet(frozen=False)  # пополнение раздела "Доступно"
        return True

    def _apply_extra_fee(self):
        self.actions.create(
            type=Action.Type.SYSTEM_MESSAGE,
            target=Action.Target.WALLET,
            amount=-self.amount,
        )
        return True

    def _apply_program_accrual(self):
        # начисление в profit программы
        if self.amount >= 0:
            action_type = Action.Type.PROFIT_ACCRUAL
        else:
            action_type = Action.Type.LOSS_CHARGEOFF
        self.actions.create(
            type=action_type, amount=self.amount, target=Action.Target.USER_PROGRAM
        )

        # ежедневные начисления начисляются в кошелёк пользователя
        withdrawal_type = self.user_program.program.withdrawal_type
        if withdrawal_type == Program.WithdrawalType.DAILY:
            self.actions.create(
                type=action_type, amount=self.amount, target=Action.Target.WALLET
            )
        return True

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

    def _to_wallet(self, frozen: bool = False):
        if self.amount:
            _type = Action.Type.TRANSFER_FROZEN if frozen else Action.Type.TRANSFER_FREE
            self.actions.create(
                type=_type,
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

    def _from_program(self, type=None):
        type = type or Action.Type.TRANSFER_BETWEEN
        self.actions.create(
            type=type,
            target=Action.Target.USER_PROGRAM,
            amount=-self.amount,
        )

    def _to_program(self):
        self.actions.create(
            type=Action.Type.TRANSFER_BETWEEN,
            target=Action.Target.USER_PROGRAM,
            amount=self.amount_free + self.amount_frozen,
        )

    def _from_wallet_to_program(self):
        self._from_wallet()
        self._to_program()

    def _from_program_to_wallet(self, frozen: bool):
        self._from_program(type=Action.Type.SYSTEM_MESSAGE)
        self._to_wallet(frozen)


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

    type = models.CharField("Тип действия", choices=Type.choices)
    name = models.CharField("Описание", max_length=127, **blank_and_null)
    target = models.CharField("Объект", choices=Target.choices)
    operation = models.ForeignKey(
        Operation,
        verbose_name="Операция",
        related_name="actions",
        on_delete=models.CASCADE,
    )
    target_name = models.CharField("Название объекта", max_length=127, **blank_and_null)
    created_at = models.DateTimeField("Дата и время", auto_now_add=True)
    amount = models.DecimalField("Сумма", **decimal_usdt)

    class Meta:
        verbose_name = "Деталь"
        verbose_name_plural = "Детали"

    def __str__(self) -> str:
        return self.name

    def apply(self):
        if self.target == self.Target.WALLET:
            if self.type == self.Type.TRANSFER_FROZEN:
                self.operation.wallet.update_balance(frozen=self.amount)
            else:
                self.operation.wallet.update_balance(free=self.amount)
        elif self.target == self.Target.USER_PROGRAM:
            if self.operation.type == Operation.Type.PROGRAM_ACCRUAL:
                self.operation.user_program.update_profit(amount=self.amount)
            else:
                self.operation.user_program.update_deposit(amount=self.amount)
            if self.operation.type == Operation.Type.PROGRAM_REPLENISHMENT:
                self.operation.replenishment.done()

    def _get_name(self):
        if self.operation.type == Operation.Type.REPLENISHMENT:
            if not self.operation.sender:
                return "Deposit"
            return f"Receipt from ID{self.operation.sender.user.id}"

        if self.operation.type == Operation.Type.WITHDRAWAL:
            return f"Request for withdrawal of {self.amount} USDT completed"

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
                if self.operation.partial:
                    return message % "partially "
                if self.operation.early_closure:
                    return message % "early "
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
            return (
                f"The program {self.operation.user_program.name} replenishment "
                f"has been {'partially ' if self.operation.partial else ''}canceled"
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
