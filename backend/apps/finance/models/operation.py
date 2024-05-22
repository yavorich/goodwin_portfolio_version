from uuid import uuid4

from django.db import models, transaction
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.timezone import now, timedelta
from django.utils.translation import gettext as _

from apps.finance.services import (
    get_wallet_settings_attr,
    send_admin_withdrawal_notifications,
)
from apps.telegram.tasks import send_template_telegram_message_task
from apps.telegram.models import MessageType as TelegramMessageType
from core.utils import blank_and_null, decimal_usdt

from .program import Program, UserProgram, UserProgramReplenishment
from .wallet import Wallet
from .frozen import FrozenItem
from .operation_history import OperationHistory
from .operation_type import OperationType, MessageType


class Operation(models.Model):
    Type = OperationType

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
    commission = models.DecimalField("Комиссия", **decimal_usdt, **blank_and_null)
    amount_net = models.DecimalField(
        "Сумма с учётом комиссии", **decimal_usdt, **blank_and_null
    )
    created_at = models.DateTimeField("Дата и время", default=timezone.now)
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
        verbose_name = "транзакцию"
        verbose_name_plural = "Транзакции"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return Operation.Type(self.type).label

    @property
    def confirmed(self):
        return self.confirmations.count() == 0

    def apply(self):
        with transaction.atomic():
            done = getattr(self, f"_apply_{self.type}")()
            self.done = done
            self.save()

    def _apply_replenishment(self):  # ready
        commission_pct = get_wallet_settings_attr(
            self.wallet, "commission_on_replenish"
        )
        self.commission = self.amount * commission_pct / 100
        self.amount_net = self.amount - self.commission
        self.save()
        return False

    def _apply_withdrawal(self):  # ready
        self.wallet.update_balance(free=-self.amount)

        commission_pct = get_wallet_settings_attr(self.wallet, "commission_on_withdraw")
        self.commission = self.amount * commission_pct / 100
        self.amount_net = self.amount - self.commission
        self.save()

        withdrawal_request = WithdrawalRequest.objects.create(
            operation=self,
            wallet=self.wallet,
            original_amount=self.amount,
            commission=self.commission,
            amount=self.amount_net,
            address=self.address,
            status=WithdrawalRequest.Status.PENDING,
        )
        send_admin_withdrawal_notifications(withdrawal_request)
        self.add_history(
            type=OperationHistory.Type.WITHDRAWAL,
            message_type=MessageType.WITHDRAWAL_REQUEST_CREATED,
            insertion_data=dict(amount=float(self.amount)),
            target_name=self.wallet.name,
            amount=-self.amount,
        )
        if telegram_id := self.wallet.user.telegram_id:
            send_template_telegram_message_task.delay(
                telegram_id,
                message_type=TelegramMessageType.WITHDRAWAL_REQUEST,
                insertion_data={
                    "amount": withdrawal_request.original_amount,
                    "commission_amount": withdrawal_request.commission,
                    "amount_with_commission": withdrawal_request.amount,
                    "transfer address": withdrawal_request.address,
                    "email": self.wallet.user.email,
                },
            )

        return False

    def _apply_transfer(self):  # ready
        self.wallet.update_balance(free=-self.amount_free, frozen=-self.amount_frozen)

        commission_pct = get_wallet_settings_attr(self.wallet, "commission_on_transfer")
        commission_free = self.amount_free * commission_pct / 100
        commission_frozen = self.amount_frozen * commission_pct / 100

        amount_free_net = self.amount_free - commission_free
        amount_frozen_net = self.amount_frozen - commission_frozen

        self.receiver.update_balance(
            free=amount_free_net,
            frozen=amount_frozen_net,
        )
        self.commission = commission_free + commission_frozen
        self.amount_net = amount_free_net + amount_frozen_net
        self.save()

        if self.amount_free:
            self.add_history(
                type=OperationHistory.Type.TRANSFER_FREE,
                message_type=MessageType.TRANSFER_SENT,
                insertion_data=dict(user_id=self.wallet.user.id),
                target_name=self.receiver.name,
                amount=-self.amount_free,
            )
            self.add_history(
                type=OperationHistory.Type.TRANSFER_FREE,
                message_type=MessageType.TRANSFER_RECEIVED,
                insertion_data=dict(user_id=self.wallet.user.id),
                target_name=self.receiver.name,
                amount=amount_free_net,
                wallet=self.receiver,
            )
            if telegram_id := self.receiver.user.telegram_id:
                send_template_telegram_message_task.delay(
                    telegram_id,
                    message_type=TelegramMessageType.INTERNAL_TRANSFER_FOR_RECIPIENT,
                    insertion_data={
                        "user_id": self.wallet.user.id,
                        "amount": amount_free_net,
                        "section": _("Free"),
                    },
                )
        if self.amount_frozen:
            self.add_history(
                type=OperationHistory.Type.TRANSFER_FROZEN,
                message_type=MessageType.TRANSFER_SENT,
                insertion_data=dict(user_id=self.wallet.user.id),
                target_name=self.receiver.name,
                amount=-self.amount_frozen,
            )
            self.add_history(
                type=OperationHistory.Type.TRANSFER_FROZEN,
                message_type=MessageType.TRANSFER_RECEIVED,
                insertion_data=dict(user_id=self.wallet.user.id),
                target_name=self.receiver.name,
                amount=amount_frozen_net,
                wallet=self.receiver,
            )
            if telegram_id := self.receiver.user.telegram_id:
                send_template_telegram_message_task.delay(
                    telegram_id,
                    message_type=TelegramMessageType.INTERNAL_TRANSFER_FOR_RECIPIENT,
                    insertion_data={
                        "user_id": self.wallet.user.id,
                        "amount": amount_frozen_net,
                        "section": _("Frozen"),
                    },
                )

        if telegram_id := self.wallet.user.telegram_id:
            send_template_telegram_message_task.delay(
                telegram_id,
                message_type=TelegramMessageType.INTERNAL_TRANSFER_FOR_SENDER,
                insertion_data={
                    "user_id": self.receiver.user.id,
                    "amount": self.amount_net,
                    "email": self.wallet.user.email,
                },
            )
        return True

    def _apply_partner_bonus(self):  # ready
        self.wallet.update_balance(amount_free=self.amount)
        self.add_history(
            type=OperationHistory.Type.LOYALTY_PROGRAM,
            message_type=MessageType.BRANCH_INCOME,
            target_name=self.wallet.name,
            amount=self.amount,
        )
        return True

    def _apply_program_start(self):  # ready
        total_amount = self.amount_free + self.amount_frozen

        self.wallet.update_balance(free=-self.amount_free, frozen=-self.amount_frozen)
        self.user_program = UserProgram.objects.create(
            wallet=self.wallet,
            program=self.program,
        )
        self.user_program.update_deposit(amount=total_amount)

        insertion_data = dict(program_name=self.user_program.name)
        self.add_history(
            type=OperationHistory.Type.TRANSFER_BETWEEN,
            message_type=MessageType.PROGRAM_START,
            target_name=self.wallet.name,
            amount=-total_amount,
            insertion_data=insertion_data,
        )
        self.add_history(
            type=OperationHistory.Type.TRANSFER_BETWEEN,
            message_type=MessageType.PROGRAM_REPLENISHED,
            target_name=self.user_program.name,
            amount=total_amount,
            insertion_data=insertion_data,
        )
        if telegram_id := self.wallet.user.telegram_id:
            send_template_telegram_message_task.delay(
                telegram_id,
                message_type=TelegramMessageType.PROGRAM_START,
                insertion_data={
                    "program_name": self.user_program.name,
                    "start_date": self.user_program.start_date,
                    "underlying_asset": self.user_program.deposit,
                    "email": self.wallet.user.email,
                },
            )
        return True

    def _apply_program_closure(self):  # ready
        insertion_data = dict(program_name=self.user_program.name)
        if self.partial:
            message_type = MessageType.PROGRAM_CLOSURE_PARTIAL
            self.user_program.update_deposit(amount=-self.amount)
        else:
            if self.early_closure:
                message_type = MessageType.PROGRAM_CLOSURE_EARLY
            else:
                message_type = MessageType.PROGRAM_CLOSURE
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
                )
        self.wallet.update_balance(frozen=self.amount)
        self.add_history(
            type=OperationHistory.Type.SYSTEM_MESSAGE,
            message_type=message_type,
            target_name=self.user_program.name,
            amount=-self.amount,
            insertion_data=insertion_data,
        )
        self.add_history(
            type=OperationHistory.Type.TRANSFER_FROZEN,
            message_type=MessageType.DEPOSIT_TRANSFER,
            target_name=self.wallet.name,
            amount=self.amount,
            insertion_data=insertion_data,
        )

        defrost_days = get_wallet_settings_attr(self.wallet, "defrost_days")
        extra_fee = get_wallet_settings_attr(self.wallet, "extra_fee")

        if telegram_id := self.wallet.user.telegram_id:
            send_template_telegram_message_task.delay(
                telegram_id,
                message_type=TelegramMessageType.PROGRAM_CLOSING,
                insertion_data={
                    "program_name": self.user_program.name,
                    "defrost_date": now().date() + timedelta(days=defrost_days),
                    "amount": self.amount,
                    "extra_fee_percent": extra_fee,
                    "email": self.wallet.user.email,
                },
            )
        return True

    def _apply_program_replenishment(self):  # ready
        total_amount = self.amount_free + self.amount_frozen
        self.wallet.update_balance(free=-self.amount_free, frozen=-self.amount_frozen)
        self.replenishment = UserProgramReplenishment.objects.create(
            program=self.user_program,
            amount=total_amount,
        )
        self.add_history(
            type=OperationHistory.Type.TRANSFER_BETWEEN,
            message_type=MessageType.TRANSFER_TO_PROGRAM,
            target_name=self.wallet.name,
            amount=-total_amount,
            insertion_data={"program_name": self.user_program.name},
        )
        return False

    def _apply_program_replenishment_cancel(self):  # ready
        program_name = self.replenishment.program.name
        insertion_data = {"program_name": program_name}

        if self.partial:
            message_type = MessageType.PROGRAM_REPLENISHMENT_CANCEL_PARTIAL
            self.replenishment.decrease(self.amount)
        else:
            message_type = MessageType.PROGRAM_REPLENISHMENT_CANCEL
            self.replenishment.cancel()

        self.wallet.update_balance(frozen=self.amount)
        self.add_history(
            type=OperationHistory.Type.SYSTEM_MESSAGE,
            message_type=message_type,
            target_name=program_name,
            amount=-self.amount,
            insertion_data=insertion_data,
        )
        self.add_history(
            type=OperationHistory.Type.TRANSFER_FROZEN,
            message_type=MessageType.DEPOSIT_TRANSFER,
            target_name=self.wallet.name,
            amount=self.amount,
            insertion_data=insertion_data,
        )

        defrost_days = get_wallet_settings_attr(self.wallet, "defrost_days")
        extra_fee = get_wallet_settings_attr(self.wallet, "extra_fee")

        if telegram_id := self.wallet.user.telegram_id:
            send_template_telegram_message_task.delay(
                telegram_id,
                message_type=TelegramMessageType.CANCELING_PROGRAM_REPLENISHMENT,
                insertion_data={
                    "program_name": program_name,
                    "available_date": now().date() + timedelta(days=defrost_days),
                    "extra_fee_percent": extra_fee,
                    "email": self.wallet.user.email,
                },
            )
        return True

    def _apply_defrost(self):  # ready
        if self.frozen_item:
            message_type = MessageType.FROZEN_AVAILABLE
            insertion_data = {"frost_date": self.frozen_item.frost_date}
            self.wallet.update_balance(
                frozen=-self.amount, item=self.frozen_item  # разморозка frozen-item
            )
            if telegram_id := self.wallet.user.telegram_id:
                send_template_telegram_message_task.delay(
                    telegram_id,
                    message_type=TelegramMessageType.FROZEN_AVAILABLE,
                    insertion_data={
                        "frozen_date": self.frozen_item.frost_date,
                        "frozen_amount": self.frozen_item.amount,
                    },
                )
        else:
            message_type = MessageType.FORCE_DEFROST
            insertion_data = None
            self.wallet.update_balance(frozen=-self.amount)  # разморозка суммы

            # списание Extra Fee
            extra_fee = get_wallet_settings_attr(self.wallet, "extra_fee")
            extra_fee_amount = self.amount * extra_fee / 100
            Operation.objects.create(
                type=Operation.Type.EXTRA_FEE,
                wallet=self.wallet,
                amount=extra_fee_amount,
            )
            if telegram_id := self.wallet.user.telegram_id:
                send_template_telegram_message_task.delay(
                    telegram_id,
                    message_type=TelegramMessageType.PREMATURE_DEFROST,
                    insertion_data={
                        "amount": self.amount,
                        "extra_fee_percent": extra_fee,
                        "extra_fee_amount": extra_fee_amount,
                        "amount_with_extra_fee": self.amount - extra_fee_amount,
                    },
                )

        self.wallet.update_balance(free=self.amount)
        self.add_history(
            type=OperationHistory.Type.TRANSFER_BETWEEN,
            message_type=message_type,
            target_name=self.wallet.name,
            amount=self.amount,
            insertion_data=insertion_data,
        )
        return True

    def _apply_extra_fee(self):  # ready
        self.wallet.update_balance(free=-self.amount)
        self.add_history(
            type=OperationHistory.Type.SYSTEM_MESSAGE,
            message_type=MessageType.EXTRA_FEE,
            target_name=self.wallet.name,
            amount=-self.amount,
        )
        return True

    def _apply_program_accrual(self):  # ready
        withdrawal_type = self.user_program.program.withdrawal_type
        self.user_program.update_profit(amount=self.amount)

        if self.amount >= 0:
            telegram_message_type = TelegramMessageType.PROGRAM_PROFIT
            if withdrawal_type == Program.WithdrawalType.DAILY:
                self.wallet.update_balance(free=self.amount)
                self.add_history(
                    type=OperationHistory.Type.SYSTEM_MESSAGE,
                    message_type=MessageType.PROGRAM_ACCRUAL_PROFIT,
                    target_name=self.wallet.name,
                    amount=self.amount,
                    insertion_data={"program_name": self.user_program.name},
                )
        else:
            telegram_message_type = TelegramMessageType.PROGRAM_LOSS
            self.add_history(
                type=OperationHistory.Type.SYSTEM_MESSAGE,
                message_type=MessageType.PROGRAM_ACCRUAL_LOSS,
                target_name=self.user_program.name,
                amount=self.amount,
            )

        if telegram_id := self.wallet.user.telegram_id:
            send_template_telegram_message_task.delay(
                telegram_id,
                message_type=telegram_message_type,
                insertion_data={
                    "program_name": self.user_program.name,
                    "yesterday_profit": self.user_program.yesterday_profit,
                    "yesterday_profit_percent": (
                        self.user_program.yesterday_profit_percent
                    ),
                    "all_profit": self.user_program.profit,
                    "all_profit_percent": self.user_program.profit_percent,
                    "underlying_asset": self.user_program.deposit,
                    "email": self.wallet.user.email,
                },
            )

        return True

    def add_history(
        self,
        type: OperationHistory.Type,
        message_type: MessageType,
        target_name: str,
        amount,
        insertion_data: dict | None = None,
        wallet: Wallet | None = None,
    ):
        OperationHistory.objects.create(
            wallet=wallet or self.wallet,
            type=type,
            message_type=message_type,
            operation_type=self.type,
            target_name=target_name,
            amount=amount,
            insertion_data=insertion_data,
        )


class WithdrawalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидание"
        APPROVED = "approved", "Одобрена"
        REJECTED = "rejected", "Отклонена"

    operation = models.ForeignKey(
        Operation,
        on_delete=models.CASCADE,
        verbose_name="Заявки на вывод",
        related_name="withdrawal_requests",
        **blank_and_null,
    )
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        verbose_name="ID",
        related_name="withdrawal_requests",
    )
    original_amount = models.DecimalField("Списать с кошелька", **decimal_usdt)
    commission = models.DecimalField("Удержать комиссию", **decimal_usdt)
    amount = models.DecimalField("Перевести инвестору", **decimal_usdt)
    address = models.CharField(
        "Адрес криптокошелька", validators=[RegexValidator(regex=r"T[A-Za-z1-9]{33}")]
    )
    status = models.CharField(
        choices=Status.choices,
        verbose_name="Статус",
    )
    created_at = models.DateField("Поставлено на вывод", default=timezone.now)
    reject_message = models.TextField("Причина отказа", blank=True)
    done = models.BooleanField("Выполнено", default=False)
    done_at = models.DateField("Дата выполнения", **blank_and_null)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки на вывод средств"

    @classmethod
    def notify_count(cls):
        return cls.objects.filter(status=cls.Status.PENDING).count()


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


class OperationSummary(Operation):
    class Meta:
        proxy = True
        verbose_name = "Транзакции"
        verbose_name_plural = "Транзакции"
