from uuid import uuid4
from decimal import Decimal

from django.db import models, transaction
from django.core.validators import RegexValidator
from django.utils import timezone, translation
from django.utils.timezone import now, timedelta
from django.utils.translation import gettext as _

from apps.finance.services import (
    get_wallet_settings_attr,
    send_admin_withdrawal_notifications,
)
from apps.finance.services.commissions import add_commission_to_history
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
        if self.type:
            return str(OperationType(self.type).label)
        return "-"

    @property
    def confirmed(self):
        return self.confirmations.count() == 0

    def apply(self):
        with transaction.atomic():
            done = getattr(self, f"_apply_{self.type}")()
            self.done = done
            self.save()

    def _apply_replenishment(self):  # ready
        self._apply_commission(attr="commission_on_replenish", included=False)
        return False

    def _apply_withdrawal(self):  # ready
        self._apply_commission(attr="commission_on_withdraw", included=True)
        self.wallet.update_balance(free=-self.amount)

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
                    "transfer_address": withdrawal_request.address,
                    "email": self.wallet.user.email,
                },
                language=translation.get_language(),
            )

        return False

    def _apply_transfer(self):  # ready
        # в таком порядке чтобы не пересчитывать атрибуты
        self._apply_transfer_receive()
        self._apply_transfer_send()
        return True

    def _apply_commission(self, attr, included=True):
        commission_rate = get_wallet_settings_attr(self.wallet, attr) / 100

        sum_amount = Decimal("0.0")
        for section in [None, "free", "frozen"]:
            amount_attr = f"amount_{section}" if section else "amount"
            if amount := getattr(self, amount_attr):
                if not included:
                    setattr(self, amount_attr, amount * (1 + commission_rate))
                sum_amount += amount

        self.commission = sum_amount * commission_rate
        self.amount_net = sum_amount - self.commission if included else sum_amount
        self.save()

    def _apply_transfer_send(self):
        self._apply_commission(attr="commission_on_transfer", included=False)
        add_commission_to_history(
            commission_type=OperationType.TRANSFER_FEE, amount=self.commission
        )

        self.wallet.update_balance(free=-self.amount_free, frozen=-self.amount_frozen)

        for section in ["free", "frozen"]:
            if amount := getattr(self, f"amount_{section}"):
                self.add_history(
                    type=getattr(OperationHistory.Type, f"TRANSFER_{section.upper()}"),
                    message_type=MessageType.TRANSFER_SENT,
                    insertion_data=dict(user_id=self.wallet.user.id),
                    target_name=self.receiver.name,
                    amount=-amount,
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
                language=translation.get_language(),
            )

    def _apply_transfer_receive(self):
        self.receiver.update_balance(free=self.amount_free, frozen=self.amount_frozen)

        for section in ["free", "frozen"]:
            if amount := getattr(self, f"amount_{section}"):
                self.add_history(
                    type=getattr(OperationHistory.Type, f"TRANSFER_{section.upper()}"),
                    message_type=MessageType.TRANSFER_RECEIVED,
                    insertion_data=dict(user_id=self.wallet.user.id),
                    target_name=self.receiver.name,
                    amount=amount,
                    wallet=self.receiver,
                )
                if telegram_id := self.receiver.user.telegram_id:
                    send_template_telegram_message_task.delay(
                        telegram_id,
                        message_type=(
                            TelegramMessageType.INTERNAL_TRANSFER_FOR_RECIPIENT
                        ),
                        insertion_data={
                            "user_id": self.wallet.user.id,
                            "amount": amount,
                            "section": _(section.capitalize()),
                        },
                        language=translation.get_language(),
                    )

    def _apply_branch_income(self):  # ready
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
                language=translation.get_language(),
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
                language=translation.get_language(),
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
                language=translation.get_language(),
            )
        return True

    def _apply_defrost(self):  # ready
        if self.frozen_item:
            message_type = MessageType.FROZEN_AVAILABLE
            insertion_data = {
                "frost_date": self.frozen_item.frost_date.strftime("%d.%m.%Y")
            }
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
                    language=translation.get_language(),
                )
        else:
            message_type = MessageType.FORCE_DEFROST
            insertion_data = None
            self.wallet.update_balance(frozen=-self.amount)  # разморозка суммы

            # списание Extra Fee
            extra_fee = get_wallet_settings_attr(self.wallet, "extra_fee")
            extra_fee_amount = self.amount * extra_fee / 100
            Operation.objects.create(
                type=Operation.Type.EXTRA_FEE_WRITEOFF,
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
                    language=translation.get_language(),
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

    def _apply_extra_fee_writeoff(self):  # ready
        self.wallet.update_balance(free=-self.amount)
        self.add_history(
            type=OperationHistory.Type.SYSTEM_MESSAGE,
            message_type=MessageType.EXTRA_FEE,
            target_name=self.wallet.name,
            amount=-self.amount,
        )
        add_commission_to_history(
            commission_type=OperationType.EXTRA_FEE, amount=self.amount
        )

    def _apply_program_accrual(self):  # ready
        withdrawal_type = self.user_program.program.withdrawal_type

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
                language=translation.get_language(),
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


class OperationSummary(Operation):
    class Meta:
        proxy = True
        verbose_name = "Транзакции"
        verbose_name_plural = "Транзакции"
