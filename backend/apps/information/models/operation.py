import random
from decimal import Decimal
from uuid import uuid4

from django.db import models, transaction
from django.core.validators import RegexValidator
from django.utils.timezone import now, timedelta

from core.utils import blank_and_null, decimal_usdt

from .program import Program, UserProgram, UserProgramReplenishment
from .wallet import Wallet
from .frozen import FrozenItem
from .operation_history import OperationHistory


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

    uuid = models.UUIDField(default=uuid4, editable=False)
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
        related_name="operation",
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
    expiration_date = models.DateField(null=True, blank=True)  # Пока что не
    # используется нигде, будет нужно для отмены слишкомдолгих транзакций при
    # начислении на кошелёк
    address = models.CharField(
        validators=[RegexValidator(regex=r"T[A-Za-z1-9]{33}")],
        **blank_and_null,
    )

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

    def _apply_replenishment(self):  # ready
        return True

    def _apply_withdrawal(self):  # soon
        self.wallet.update_balance(free=-self.amount)
        OperationHistory.objects.create(
            wallet=self.wallet,
            type=OperationHistory.Type.WITHDRAWAL,
            description="Withdrawal request accepted",
            target_name=self.wallet.name,
            amount=-self.amount,
        )
        WithdrawalRequest.objects.create(
            wallet=self.wallet,
            original_amount=self.amount,
            amount=self.amount * Decimal(0.98),
            address=self.address,
            status=WithdrawalRequest.Status.PENDING,
        )
        return True

    def _apply_transfer(self):  # ready
        self.wallet.update_balance(free=-self.amount_free, frozen=-self.amount_frozen)
        self.receiver.update_balance(free=self.amount_free, frozen=self.amount_frozen)
        if self.amount_free:
            OperationHistory.objects.create(
                wallet=self.wallet,
                type=OperationHistory.Type.TRANSFER_FREE,
                description=f"Transfer to GDW client ID{self.receiver.user.id}",
                target_name=self.receiver.name,
                amount=-self.amount_free,
            )
            OperationHistory.objects.create(
                wallet=self.receiver,
                type=OperationHistory.Type.TRANSFER_FREE,
                description=f"Receipt from ID{self.wallet.user.id}",
                target_name=self.receiver.name,
                amount=self.amount_free,
            )
        if self.amount_frozen:
            OperationHistory.objects.create(
                wallet=self.wallet,
                type=OperationHistory.Type.TRANSFER_FROZEN,
                description=f"Transfer to GDW client ID{self.receiver.user.id}",
                target_name=self.receiver.name,
                amount=-self.amount_frozen,
            )
            OperationHistory.objects.create(
                wallet=self.receiver,
                type=OperationHistory.Type.TRANSFER_FROZEN,
                description=f"Receipt from ID{self.wallet.user.id}",
                target_name=self.receiver.name,
                amount=self.amount_frozen,
            )
        return True

    def _apply_partner_bonus(self):  # ready
        self.wallet.update_balance(amount_free=self.amount)
        OperationHistory.objects.create(
            wallet=self.wallet,
            type=OperationHistory.Type.LOYALTY_PROGRAM,
            description="Branch income",
            target_name=self.wallet.name,
            amount=self.amount,
        )
        return True

    def _apply_program_start(self):  # ready
        self.wallet.update_balance(free=-self.amount_free, frozen=-self.amount_frozen)
        self.user_program = UserProgram.objects.create(
            wallet=self.wallet,
            program=self.program,
        )
        self.user_program.update_deposit(amount=self.amount_free + self.amount_frozen)
        OperationHistory.objects.create(
            wallet=self.wallet,
            type=OperationHistory.Type.TRANSFER_BETWEEN,
            description=(f"Start program {self.user_program.name}"),
            target_name=self.wallet.name,
            amount=-(self.amount_free + self.amount_frozen),
        )
        OperationHistory.objects.create(
            wallet=self.wallet,
            type=OperationHistory.Type.TRANSFER_BETWEEN,
            description=(f"Program {self.user_program.name} has been replenished"),
            target_name=self.user_program.name,
            amount=self.amount_free + self.amount_frozen,
        )
        return True

    def _apply_program_closure(self):  # ready
        message = f"Program {self.user_program.name} %sclosure"
        if self.partial:
            message = message % "partial "
            self.user_program.update_deposit(amount=-self.amount)
        else:
            message = message % ("early " if self.early_closure else "")
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
        self.wallet.update_balance(frozen=self.amount)
        OperationHistory.objects.create(
            wallet=self.wallet,
            type=OperationHistory.Type.SYSTEM_MESSAGE,
            description=message,
            target_name=self.user_program.name,
            amount=-self.amount,
        )
        OperationHistory.objects.create(
            wallet=self.wallet,
            type=OperationHistory.Type.TRANSFER_FROZEN,
            description=f"Deposit transfer {self.user_program.name}",
            target_name=self.wallet.name,
            amount=self.amount,
        )
        return True

    def _apply_program_replenishment(self):  # ready
        self.wallet.update_balance(free=-self.amount_free, frozen=-self.amount_frozen)
        self.replenishment = UserProgramReplenishment.objects.create(
            program=self.user_program,
            amount=self.amount_free + self.amount_frozen,
        )
        OperationHistory.objects.create(
            wallet=self.wallet,
            type=OperationHistory.Type.TRANSFER_BETWEEN,
            description=(f"Program {self.user_program.name} replenishment"),
            target_name=self.wallet.name,
            amount=-(self.amount_free + self.amount_frozen),
        )
        return False

    def _apply_program_replenishment_cancel(self):  # ready
        program_name = self.replenishment.program.name
        message = f"Program {program_name} replenishment has been %scanceled"
        if self.partial:
            message = message % "partially "
            self.replenishment.decrease(self.amount)
        else:
            message = message % ""
            self.replenishment.cancel()
        self.wallet.update_balance(frozen=self.amount)
        OperationHistory.objects.create(
            wallet=self.wallet,
            type=OperationHistory.Type.SYSTEM_MESSAGE,
            description=message,
            target_name=program_name,
            amount=-self.amount,
        )
        OperationHistory.objects.create(
            wallet=self.wallet,
            type=OperationHistory.Type.TRANSFER_FROZEN,
            description=f"Deposit transfer {program_name}",
            target_name=self.wallet.name,
            amount=self.amount,
        )
        return True

    def _apply_defrost(self):  # ready
        if self.frozen_item:
            message = (
                f"Frozen assets from {self.frozen_item.frost_date} have been defrosted"
            )
            self.wallet.update_balance(
                frozen=-self.amount, item=self.frozen_item  # разморозка frozen-item
            )
        else:
            message = "The defrost request has been completed"
            self.wallet.update_balance(frozen=-self.amount)  # разморозка суммы
            Operation.objects.create(
                type=Operation.Type.EXTRA_FEE,
                wallet=self.wallet,
                amount=Decimal("0.1") * self.amount,
                confirmed=True,
            )
        self.wallet.update_balance(free=self.amount)
        OperationHistory.objects.create(
            wallet=self.wallet,
            type=OperationHistory.Type.TRANSFER_BETWEEN,
            description=message,
            target_name=self.wallet.name,
            amount=self.amount,
        )
        return True

    def _apply_extra_fee(self):  # ready
        self.wallet.update_balance(free=-self.amount)
        OperationHistory.objects.create(
            wallet=self.wallet,
            type=OperationHistory.Type.SYSTEM_MESSAGE,
            description="Extra Fee commission write-off",
            target_name=self.wallet.name,
            amount=-self.amount,
        )
        return True

    def _apply_program_accrual(self):  # ready
        withdrawal_type = self.user_program.program.withdrawal_type
        self.user_program.update_profit(amount=self.amount)

        if self.amount >= 0:
            if withdrawal_type == Program.WithdrawalType.DAILY:
                self.wallet.update_balance(free=self.amount)
                OperationHistory.objects.create(
                    wallet=self.wallet,
                    type=OperationHistory.Type.SYSTEM_MESSAGE,
                    description=f"Accrual by program {self.user_program.name}",
                    target_name=self.wallet.name,
                    amount=self.amount,
                )
        else:
            self.user_program.update_profit(amount=self.amount)
            OperationHistory.objects.create(
                wallet=self.wallet,
                type=OperationHistory.Type.SYSTEM_MESSAGE,
                description=f"Loss by program {self.user_program.name}",
                target_name=self.user_program.name,
                amount=self.amount,
            )

        return True


class WithdrawalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидание"
        APPROVED = "approved", "Одобрена"
        REJECTED = "rejected", "Отклонена"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        verbose_name="Кошелёк",
        related_name="withdrawal_requests",
    )
    original_amount = models.DecimalField("Сумма без учета комиссии", **decimal_usdt)
    amount = models.DecimalField("Сумма c учётом комиссии", **decimal_usdt)
    address = models.CharField(
        "Адрес TRC-20", validators=[RegexValidator(regex=r"T[A-Za-z1-9]{33}")]
    )
    status = models.CharField(
        choices=Status.choices,
        verbose_name="Статус заявки",
    )
    reject_message = models.TextField(blank=True, verbose_name="Причина отказа")
    done = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки на вывод средств"


# TODO: удалить модель
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
