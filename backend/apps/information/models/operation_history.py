from django.db import models
from django.utils.translation import gettext_lazy as _

from .wallet import Wallet
from core.utils import blank_and_null, decimal_usdt
from core.localized.fields import LocalizedCharField


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

    # class Message(models.TextChoices):
    #     DEPOSIT = _("")
    wallet = models.ForeignKey(
        Wallet,
        verbose_name="Кошелёк",
        related_name="operations_history",
        on_delete=models.CASCADE,
    )
    type = models.CharField("Тип операции", choices=Type.choices)
    description = LocalizedCharField("Описание", max_length=127, **blank_and_null)
    target_name = models.CharField("Название объекта", max_length=127, **blank_and_null)
    created_at = models.DateTimeField("Дата и время", auto_now_add=True)
    amount = models.DecimalField("Сумма", **decimal_usdt, **blank_and_null)

    class Meta:
        verbose_name = "История операций"
        verbose_name_plural = "Истории операций"
        ordering = ["-created_at"]
