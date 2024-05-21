from django.db.models import TextChoices


class OperationType(TextChoices):
    REPLENISHMENT = "replenishment", "Пополнение"
    WITHDRAWAL = "withdrawal", "Снятие"
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
