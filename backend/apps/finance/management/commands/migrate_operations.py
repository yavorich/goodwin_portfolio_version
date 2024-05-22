from django.core.management.base import BaseCommand

from apps.finance.models import (
    OperationHistory,
    FrozenItem,
)
from apps.finance.models.operation_type import OperationType, MessageType


class Command(BaseCommand):
    def handle(self, *args, **options):
        history = OperationHistory.objects.filter(message_type__isnull=True)

        for o in history.filter(description__ru="Заявка на вывод принята"):
            o.operation_type = OperationType.WITHDRAWAL
            o.message_type = MessageType.WITHDRAWAL_REQUEST_CREATED
            o.save()
        for o in history.filter(description__ru__icontains="USDT исполнена"):
            o.operation_type = OperationType.WITHDRAWAL
            o.message_type = MessageType.WITHDRAWAL_REQUEST_APPROVED
            o.insertion_data = {"amount": float(o.amount)}
            o.save()
        for o in history.filter(description__ru__icontains="USDT отклонена"):
            o.operation_type = OperationType.WITHDRAWAL
            o.message_type = MessageType.WITHDRAWAL_REQUEST_REJECTED
            o.insertion_data = {"amount": float(o.amount)}
            o.save()
        for o in history.filter(description__ru="Депозит"):
            o.operation_type = OperationType.REPLENISHMENT
            o.message_type = MessageType.REPLENISHMENT
            o.save()
        for o in history.filter(description__ru="Списание комиссии Extra Fee"):
            o.operation_type = OperationType.EXTRA_FEE
            o.message_type = MessageType.EXTRA_FEE
            o.save()
        for o in history.filter(
            description__ru="Заявка на разморозку активов исполнена"
        ):
            o.operation_type = OperationType.DEFROST
            o.message_type = MessageType.FORCE_DEFROST
            o.save()
        for o in history.filter(description__ru__icontains="разморожены"):
            o.operation_type = OperationType.DEFROST
            o.message_type = MessageType.FROZEN_AVAILABLE
            frozen_item = FrozenItem.objects.filter(amount=o.amount).first()
            o.insertion_data = {
                "frost_date": frozen_item.frost_date.strftime("%d.%m.%Y")
            }
            o.save()
        for o in history.filter(description__ru__icontains="Перевод депозита"):
            o.operation_type = OperationType.PROGRAM_CLOSURE
            o.message_type = MessageType.DEPOSIT_TRANSFER
            o.insertion_data = {"program_name": o.description.ru.split(" ")[-1]}
            o.save()
        for o in history.filter(description__ru="Branch income"):
            o.operation_type = OperationType.PARTNER_BONUS
            o.message_type = MessageType.BRANCH_INCOME
            o.save()
        for o in history.filter(description__ru="Списание отрицательной прибыли"):
            o.operation_type = OperationType.PROGRAM_ACCRUAL
            o.message_type = MessageType.PROGRAM_ACCRUAL_LOSS
            o.save()
        for o in history.filter(description__ru__icontains="Начисление по программе"):
            o.operation_type = OperationType.PROGRAM_ACCRUAL
            o.message_type = MessageType.PROGRAM_ACCRUAL_PROFIT
            o.insertion_data = {"program_name": o.description.ru.split(" ")[-1]}
            o.save()
        for o in history.filter(
            description__ru__icontains="Частичное закрытие программы"
        ):
            o.operation_type = OperationType.PROGRAM_CLOSURE
            o.message_type = MessageType.PROGRAM_CLOSURE_PARTIAL
            o.insertion_data = {"program_name": o.description.ru.split(" ")[-1]}
            o.save()
        for o in history.filter(description__ru__icontains="закрыта досрочно"):
            o.operation_type = OperationType.PROGRAM_CLOSURE
            o.message_type = MessageType.PROGRAM_CLOSURE_EARLY
            o.insertion_data = {"program_name": o.description.ru.split(" ")[1]}
            o.save()
        for o in history.filter(description__ru__icontains="закрыта"):
            if o.message_type is None:
                o.operation_type = OperationType.PROGRAM_CLOSURE
                o.message_type = MessageType.PROGRAM_CLOSURE
                o.insertion_data = {"program_name": o.description.ru.split(" ")[1]}
                o.save()
        for o in history.filter(
            description__ru__icontains="Частичная отмена пополнения программы"
        ):
            o.operation_type = OperationType.PROGRAM_REPLENISHMENT_CANCEL
            o.message_type = MessageType.PROGRAM_REPLENISHMENT_CANCEL_PARTIAL
            o.insertion_data = {"program_name": o.description.ru.split(" ")[-1]}
            o.save()
        for o in history.filter(
            description__ru__icontains="Отмена пополнения программы"
        ):
            if o.message_type is None:
                o.operation_type = OperationType.PROGRAM_REPLENISHMENT_CANCEL
                o.message_type = MessageType.PROGRAM_REPLENISHMENT_CANCEL
                o.insertion_data = {"program_name": o.description.ru.split(" ")[-1]}
                o.save()
        for o in history.filter(description__ru__icontains="пополнена"):
            o.operation_type = OperationType.PROGRAM_REPLENISHMENT
            o.message_type = MessageType.PROGRAM_REPLENISHED
            o.insertion_data = {"program_name": o.description.ru.split(" ")[1]}
            o.save()
        for o in history.filter(description__ru__icontains="Запуск программы"):
            o.operation_type = OperationType.PROGRAM_START
            o.message_type = MessageType.PROGRAM_START
            o.insertion_data = {"program_name": o.description.ru.split(" ")[-1]}
            o.save()
        for o in history.filter(description__ru__icontains="Перевод в программу"):
            o.operation_type = OperationType.PROGRAM_REPLENISHMENT
            o.message_type = MessageType.TRANSFER_TO_PROGRAM
            o.insertion_data = {"program_name": o.description.ru.split(" ")[-1]}
            o.save()
        for o in history.filter(description__ru__icontains="Поступление от ID"):
            o.operation_type = OperationType.TRANSFER
            o.message_type = MessageType.TRANSFER_RECEIVED
            o.insertion_data = {"user_id": o.description.ru.split(" ")[-1][2:]}
            o.save()
        for o in history.filter(description__ru__icontains="Перевод клиенту GDW ID"):
            o.operation_type = OperationType.TRANSFER
            o.message_type = MessageType.TRANSFER_SENT
            o.insertion_data = {"user_id": o.description.ru.split(" ")[-1][2:]}
            o.save()
        for o in history.filter(description__ru__icontains="Перевод клиенту GDW ID"):
            o.operation_type = OperationType.TRANSFER
            o.message_type = MessageType.TRANSFER_SENT
            o.insertion_data = {"user_id": o.description.ru.split(" ")[-1][2:]}
            o.save()
        OperationHistory.objects.filter(message_type__isnull=True).delete()
