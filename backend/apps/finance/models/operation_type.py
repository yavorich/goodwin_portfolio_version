from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class OperationType(TextChoices):
    REPLENISHMENT = "replenishment", _("Пополнение")
    WITHDRAWAL = "withdrawal", _("Снятие")
    TRANSFER = "transfer", _("Перевод")
    BRANCH_INCOME = "branch_income", _("Доход филиала")
    PROGRAM_START = "program_start", _("Запуск программы")
    PROGRAM_CLOSURE = "program_closure", _("Закрытие программы")
    PROGRAM_REPLENISHMENT = "program_replenishment", _("Пополнение программы")
    PROGRAM_REPLENISHMENT_CANCEL = (
        "program_replenishment_cancel",
        _("Отмена пополнения программы"),
    )
    DEFROST = "defrost", _("Разморозка активов")
    EXTRA_FEE_WRITEOFF = "extra_fee_writeoff", _("Списание комиссии Extra Fee")
    PROGRAM_ACCRUAL = "program_accrual", _("Начисление по программе")

    # Операции начисления комиссий для бизнес-аккаунта
    REPLENISHMENT_FEE = "replenishment_fee", _("Комиссия с пополнений")
    WITHDRAWAL_FEE = "withdrawal_fee", _("Комиссия со снятий")
    TRANSFER_FEE = "transfer_fee", _("Комиссия с внутренних переводов")
    SUCCESS_FEE = "success_fee", _("Success fee")
    MANAGEMENT_FEE = "management_fee", _("Management fee")
    EXTRA_FEE = "extra_fee", _("Extra fee")


class MessageType(TextChoices):
    WITHDRAWAL_REQUEST_CREATED = "withdrawal_request_created", "Заявка на вывод создана"
    WITHDRAWAL_REQUEST_APPROVED = (
        "withdrawal_request_approved",
        "Заявка на вывод подтверждена",
    )
    WITHDRAWAL_REQUEST_REJECTED = (
        "withdrawal_request_rejected",
        "Заявка на вывод отклонена",
    )
    TRANSFER_SENT = "transfer_sent", "Внутренний перевод отправлен"
    TRANSFER_RECEIVED = "transfer_received", "Внутренний перевод получен"
    TRANSFER_TO_PROGRAM = "transfer_to_program", "Перевод в программу"
    PROGRAM_START = "program_start", "Запуск программы"
    PROGRAM_REPLENISHED = "program_replenished", "Программа пополнена"
    PROGRAM_REPLENISHMENT_CANCEL = (
        "program_replenishment_cancel",
        "Отмена пополнения программы",
    )
    PROGRAM_REPLENISHMENT_CANCEL_PARTIAL = (
        "program_replenishment_cancel_partial",
        "Частичная отмена пополнения программы",
    )
    PROGRAM_CLOSURE = "program_closed", "Закрытие программы"
    PROGRAM_CLOSURE_EARLY = "program_closed_early", "Досрочное закрытие программы"
    PROGRAM_CLOSURE_PARTIAL = "program_closure_partial", "Частичное закрытие программы"
    PROGRAM_ACCRUAL_PROFIT = "program_accrual_profit", "Прибыль по программе"
    PROGRAM_ACCRUAL_LOSS = "program_accrual_loss", "Отрицательная прибыль по программе"
    BRANCH_INCOME = "branch_income", "Доход филиала"
    DEPOSIT_TRANSFER = "deposit_transfer", "Вывод депозита из программы"
    FROZEN_AVAILABLE = "frozen_available", "Разморозка средств"
    FORCE_DEFROST = "force_defrost", "Досрочная разморозка средств"
    EXTRA_FEE = "extra_fee", "Списание Extra Fee"
    REPLENISHMENT = "replenishment", "Пополнение кошелька"


DATA_INSERTION = {
    MessageType.WITHDRAWAL_REQUEST_APPROVED: {
        "amount": "Сумма без учёта комиссии",
    },
    MessageType.WITHDRAWAL_REQUEST_REJECTED: {
        "amount": "Сумма без учёта комиссии",
    },
    MessageType.TRANSFER_SENT: {
        "user_id": "ID пользователя",
    },
    MessageType.TRANSFER_RECEIVED: {
        "user_id": "ID пользователя",
    },
    MessageType.PROGRAM_START: {
        "program_name": "Название программы",
    },
    MessageType.PROGRAM_REPLENISHED: {
        "program_name": "Название программы",
    },
    MessageType.PROGRAM_CLOSURE_PARTIAL: {
        "program_name": "Название программы",
    },
    MessageType.PROGRAM_CLOSURE_EARLY: {
        "program_name": "Название программы",
    },
    MessageType.PROGRAM_CLOSURE: {
        "program_name": "Название программы",
    },
    MessageType.DEPOSIT_TRANSFER: {
        "program_name": "Название программы",
    },
    MessageType.TRANSFER_TO_PROGRAM: {
        "program_name": "Название программы",
    },
    MessageType.PROGRAM_REPLENISHMENT_CANCEL: {
        "program_name": "Название программы",
    },
    MessageType.PROGRAM_REPLENISHMENT_CANCEL_PARTIAL: {
        "program_name": "Название программы",
    },
    MessageType.FROZEN_AVAILABLE: {
        "frost_date": "Дата заморозки",
    },
    MessageType.PROGRAM_ACCRUAL_PROFIT: {
        "program_name": "Название программы",
    },
}

INITIAL_MESSAGE_TYPES = {
    MessageType.WITHDRAWAL_REQUEST_CREATED: dict(
        ru="Заявка на вывод принята",
        en="Withdrawal request accepted",
        cn="",
    ),
    MessageType.WITHDRAWAL_REQUEST_APPROVED: dict(
        ru="Заявка на вывод {amount} USDT исполнена",
        en=("The withdrawal request of {amount}" "USDT has been processed."),
        cn="",
    ),
    MessageType.WITHDRAWAL_REQUEST_REJECTED: dict(
        ru="Заявка на вывод {amount} USDT отклонена",
        en=("The withdrawal request of {amount}" "USDT has been rejected."),
        cn="",
    ),
    MessageType.TRANSFER_SENT: dict(
        ru="Перевод клиенту GDW ID{user_id}",
        en="Transfer to GDW client ID{user_id}",
        cn="",
    ),
    MessageType.TRANSFER_RECEIVED: dict(
        ru="Поступление от ID{user_id}",
        en="Receipt from ID{user_id}",
        cn="",
    ),
    MessageType.BRANCH_INCOME: dict(
        ru="Доход филиала",
        en="Branch income",
        cn="",
    ),
    MessageType.PROGRAM_START: dict(
        ru="Запуск программы {program_name}",
        en="Starting the {program_name} program",
        cn="",
    ),
    MessageType.PROGRAM_REPLENISHED: dict(
        ru="Программа {program_name} пополнена",
        en="Program {program_name} has been replenished",
        cn="",
    ),
    MessageType.PROGRAM_CLOSURE_PARTIAL: dict(
        ru="Частичное закрытие программы {program_name}",
        en="Partial closure of the {program_name} program",
        cn="",
    ),
    MessageType.PROGRAM_CLOSURE_EARLY: dict(
        ru="Программа {program_name} закрыта досрочно",
        en="The {program_name} program is closed early",
        cn="",
    ),
    MessageType.PROGRAM_CLOSURE: dict(
        ru="Программа {program_name} закрыта",
        en="{program_name} program is closed",
        cn="",
    ),
    MessageType.DEPOSIT_TRANSFER: dict(
        ru="Перевод депозита {program_name}",
        en="Transfer of deposit {program_name}",
        cn="",
    ),
    MessageType.TRANSFER_TO_PROGRAM: dict(
        ru="Перевод в программу {program_name}",
        en="Transfer to program {program_name}",
        cn="",
    ),
    MessageType.PROGRAM_REPLENISHMENT_CANCEL: dict(
        ru="Отмена пополнения программы {program_name}",
        en="Cancellation of the replenishment of program {program_name}",
        cn="",
    ),
    MessageType.PROGRAM_REPLENISHMENT_CANCEL_PARTIAL: dict(
        ru="Частичная отмена пополнения программы {program_name}",
        en="Partial cancellation of the replenishment of program {program_name}",
        cn="",
    ),
    MessageType.FROZEN_AVAILABLE: dict(
        ru="Замороженные активы от {frost_date} разморожены",
        en="Frozen assets from {frost_date} defrosted",
        cn="",
    ),
    MessageType.FORCE_DEFROST: dict(
        ru="Заявка на разморозку активов исполнена",
        en="The application for unfreezing of assets has been completed",
        cn="",
    ),
    MessageType.EXTRA_FEE: dict(
        ru="Списание комиссии Extra Fee",
        en="Extra Fee commission write-off",
        cn="",
    ),
    MessageType.PROGRAM_ACCRUAL_PROFIT: dict(
        ru="Начисление по программе {program_name}",
        en="Accrual under the {program_name} program",
        cn="",
    ),
    MessageType.PROGRAM_ACCRUAL_LOSS: dict(
        ru="Списание отрицательной прибыли",
        en="Write-off of negative profit",
        cn="",
    ),
    MessageType.REPLENISHMENT: dict(
        ru="Депозит",
        en="Deposit",
        cn="",
    ),
}
