from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.db import models

from core.utils import blank_and_null, add_business_days, decimal_usdt, decimal_pct


class Program(models.Model):
    class AccrualType(models.TextChoices):
        DAILY = "daily", "Ежедневно"

    class WithdrawalType(models.TextChoices):
        DAILY = "daily", "Ежедневно"
        AFTER_FINISH = "after_finish", "По окончанию срока программы"

    name = models.CharField("Название", max_length=31)
    duration = models.IntegerField("Продолжительность (мес)", **blank_and_null)
    exp_profit = models.FloatField("Ожидаемая доходность (%)")
    min_deposit = models.DecimalField("Минимальный депозит", **decimal_usdt)
    accrual_type = models.CharField("Начисление прибыли", choices=AccrualType.choices)
    withdrawal_type = models.CharField("Вывод прибыли", choices=WithdrawalType.choices)
    max_risk = models.FloatField("Максимальный риск (%)")
    success_fee = models.DecimalField("Success Fee (%)", **decimal_pct)
    management_fee = models.DecimalField(
        "Management Fee (%, в день)", max_digits=6, decimal_places=4
    )
    withdrawal_terms = models.IntegerField("Срок вывода базового актива (дней)")

    class Meta:
        verbose_name = "Программа"
        verbose_name_plural = "Программы"

    def __str__(self) -> str:
        return self.name


class ProgramResult(models.Model):
    program = models.ForeignKey(
        Program,
        verbose_name="Программа",
        related_name="results",
        on_delete=models.CASCADE,
        **blank_and_null,
    )
    result = models.DecimalField(
        "Результат программы за прошедшие сутки (%) ", **decimal_pct, default=1
    )
    created_at = models.DateTimeField("Дата и время создания", auto_now_add=True)

    class Meta:
        get_latest_by = "created_at"
        ordering = ["-created_at"]
        verbose_name = "Результат программы"
        verbose_name_plural = "Результаты программ"


class UserProgram(models.Model):
    class Status(models.TextChoices):
        INITIAL = "initial", "Ожидает запуска"
        RUNNING = "running", "Запущена"
        FINISHED = "finished", "Завершена"

    name = models.CharField("Название", max_length=31, **blank_and_null)
    wallet = models.ForeignKey(
        "Wallet",
        verbose_name="Кошелёк",
        related_name="programs",
        on_delete=models.CASCADE,
    )
    program = models.ForeignKey(
        Program,
        verbose_name="Программа",
        related_name="users",
        on_delete=models.CASCADE,
    )
    start_date = models.DateField("Дата начала", **blank_and_null)
    end_date = models.DateField("Дата завершения", **blank_and_null)
    status = models.CharField("Статус", choices=Status.choices, default=Status.INITIAL)
    deposit = models.DecimalField("Начальный депозит", **decimal_usdt, **blank_and_null)
    funds = models.DecimalField(
        "Текущие средства", **decimal_usdt, default=Decimal("0.0")
    )
    force_closed = models.BooleanField("Завершена принудительно", default=False)

    class Meta:
        verbose_name = "Программа пользователя"
        verbose_name_plural = "Программы пользователей"

    def __str__(self):
        return str(self.name)

    def _set_name(self):
        if not self.name:
            count = UserProgram.objects.filter(
                wallet=self.wallet, program=self.program
            ).count()
            self.name = self.program.name + f"/{count + 1}"

    def _set_start_date(self):
        if not self.start_date:
            self.start_date = add_business_days(3)

    def _set_end_date(self):
        if not self.end_date and (duration := self.program.duration):
            self.end_date = self.start_date + relativedelta(months=duration)

    def _set_deposit(self):
        if not self.deposit:
            self.deposit = self.funds

    def start(self):
        self.status = self.Status.RUNNING
        self.save()

    def close(self, force: bool = False):
        self.status = self.Status.FINISHED
        self.force_closed = force
        self.wallet.update_balance(frozen=self.funds)
        self.update_balance(-self.funds)
        self.save()

    def update_balance(self, amount):
        self.funds += amount
        self.save()


class UserProgramReplenishment(models.Model):
    class Status(models.TextChoices):
        INITIAL = "initial", "Ожидает исполнения"
        DONE = "done", "Исполнено"
        CANCELED = "canceled", "Отменено"

    program = models.ForeignKey(
        UserProgram,
        verbose_name="Программа",
        related_name="replenishments",
        on_delete=models.CASCADE,
    )
    operation = models.OneToOneField(
        "Operation", verbose_name="Операция", on_delete=models.CASCADE, **blank_and_null
    )
    amount = models.DecimalField("Сумма", **decimal_usdt)
    status = models.CharField("Статус", choices=Status.choices, default=Status.INITIAL)
    apply_date = models.DateField(
        "Ожидаемая дата зачисления на счет программы", **blank_and_null
    )

    def __str__(self):
        return f"Пополнение {self.program.name}"

    class Meta:
        verbose_name = "Пополнение"
        verbose_name_plural = "Пополнения программ"

    def cancel(self, amount):
        self.amount -= amount
        if self.amount == 0:
            self.status = self.Status.CANCELED
        self.save()

    def done(self):
        self.status = self.Status.DONE
        self.save()

    def _set_apply_date(self, *args, **kwargs):
        if not self.apply_date:
            self.apply_date = add_business_days(3)


class UserProgramAccrual(models.Model):
    program = models.ForeignKey(
        UserProgram,
        verbose_name="Программа",
        related_name="accruals",
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField("Сумма начисления", **decimal_usdt)
    success_fee = models.DecimalField("Сумма Success Fee", **decimal_usdt)
    created_at = models.DateField("Дата", auto_now_add=True)

    def __str__(self):
        return f"Начисление по {self.program.name}"

    class Meta:
        verbose_name = "Начисление"
        verbose_name_plural = "Начисления по программам"
