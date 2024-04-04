from django.db import models

from .wallet import Wallet
from core.utils import blank_and_null, decimal_usdt


class OperationHistory(models.Model):
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

    wallet = models.ForeignKey(
        Wallet,
        verbose_name="Кошелёк",
        related_name="operations_history",
        on_delete=models.CASCADE,
    )
    type = models.CharField("Тип операции", choices=Type.choices)
    description = models.CharField("Описание", max_length=127, **blank_and_null)
    target_name = models.CharField("Название объекта", max_length=127, **blank_and_null)
    created_at = models.DateTimeField("Дата и время", auto_now_add=True)
    amount = models.DecimalField("Сумма", **decimal_usdt)

    class Meta:
        verbose_name = "История операций"
        verbose_name_plural = "Истории операций"
