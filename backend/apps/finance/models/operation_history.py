from datetime import date
from decimal import Decimal

from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.utils import blank_and_null, decimal_usdt

from core.localized.fields import LocalizedCharField

from .operation_type import OperationType, MessageType
from .operation_message import OperationMessage


class OperationHistoryQuerySet(QuerySet):
    def total_in(self):
        return self.filter(amount__gt=0).aggregate(total=Sum("amount"))["total"] or 0

    def total_out(self):
        return self.filter(amount__lt=0).aggregate(total=Sum("amount"))["total"] or 0


class OperationHistory(models.Model):
    class Type(models.TextChoices):
        TRANSFER_FREE = "transfer_free", _('Перевод в раздел "Доступно"')
        TRANSFER_FROZEN = "transfer_frozen", _('Перевод в раздел "Заморожено"')
        TRANSFER_BETWEEN = "transfer_between", _("Перевод между счетами")
        WITHDRAWAL = "withdrawal", _("Вывод")
        REPLENISHMENT = "replenishment", _("Пополнение")
        PROFIT_ACCRUAL = "profit_accrual", _("Начисление прибыли")
        LOSS_CHARGEOFF = "loss_chargeoff", _("Фиксация убытка")
        LOYALTY_PROGRAM = "loyalty_program", _("Программа лояльности")
        SYSTEM_MESSAGE = "system_message", _("Системное сообщение")

    operation_type = models.CharField(choices=OperationType.choices, **blank_and_null)
    message_type = models.CharField(choices=MessageType.choices, **blank_and_null)
    insertion_data = models.JSONField(**blank_and_null)
    wallet = models.ForeignKey(
        "Wallet",
        verbose_name="Кошелёк",
        related_name="operations_history",
        on_delete=models.CASCADE,
    )
    type = models.CharField("Тип операции", choices=Type.choices)
    description = LocalizedCharField("Описание", max_length=127, **blank_and_null)
    target_name = models.CharField("Название объекта", max_length=127, **blank_and_null)
    created_at = models.DateTimeField(
        "Дата и время", default=timezone.now  # для парсинга внешней базы
    )
    amount = models.DecimalField("Сумма", **decimal_usdt, **blank_and_null)

    objects = OperationHistoryQuerySet.as_manager()

    class Meta:
        verbose_name = "История операций"
        verbose_name_plural = "Истории операций"
        ordering = ["-created_at"]

    def get_description(self, language=None):
        insertion_data = self.insertion_data or {}

        template_message = OperationMessage.objects.get(message_type=self.message_type)
        text = template_message.text.get(language)

        for field in template_message.insertion_iter():
            try:
                value = insertion_data[field]
            except KeyError:
                raise ValueError(f"insertion data dict must have {field}")

            if isinstance(value, date):
                value = value.strftime("%d.%m.%Y")
            elif isinstance(value, (float, Decimal)):
                value = round(value, 2)

            text = text.replace(f"{{{field}}}", str(value))
        return text
