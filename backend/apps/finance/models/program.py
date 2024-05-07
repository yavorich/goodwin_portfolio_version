from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.utils.timezone import now, timedelta, datetime

from core.utils import blank_and_null, add_business_days, decimal_usdt, decimal_pct
from .operation_history import OperationHistory


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
    # success_fee = models.DecimalField("Success Fee (%)", **decimal_pct)
    # management_fee = models.DecimalField(
    #     "Management Fee (%, в день)", max_digits=6, decimal_places=4
    # )
    withdrawal_terms = models.IntegerField("Срок вывода базового актива (дней)")

    class Meta:
        verbose_name = "Программа"
        verbose_name_plural = "Программы"

    def __str__(self) -> str:
        return self.name


class ProgramResult(models.Model):
    _singleton = models.BooleanField(default=True, editable=False, unique=True)
    result = models.DecimalField("Дневная доходность (%) ", **decimal_pct)
    until = models.DateField("Актуально до")
    apply_time = models.TimeField("Время ежедневных начислений")
    task_id = models.CharField(max_length=255, **blank_and_null)

    class Meta:
        verbose_name = "настройки начислений"
        verbose_name_plural = "Настройки начислений"

    def get_apply_datetime(self):
        apply_date = now().date() + timedelta(
            days=int(now().time() > self.apply_time)
        )
        return datetime.combine(apply_date, self.apply_time).astimezone(
            now().tzinfo
        )


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
    end_date = models.DateField("Планируемая дата завершения", **blank_and_null)
    close_date = models.DateField("Фактическая дата завершения", **blank_and_null)
    status = models.CharField("Статус", choices=Status.choices, default=Status.INITIAL)
    deposit = models.DecimalField(
        "Базовый депозит", **decimal_usdt, default=Decimal("0.0")
    )
    funds = models.DecimalField(
        "Текущие торговые средства", **decimal_usdt, default=Decimal("0.0")
    )
    profit = models.DecimalField(
        "Суммарный доход", **decimal_usdt, default=Decimal("0.0")
    )

    # для уникальности программ во время парсинга из внешней базы
    created_at = models.DateTimeField(default=timezone.now, null=True)

    class Meta:
        verbose_name = "Программа пользователя"
        verbose_name_plural = "Программы пользователей"

    def __str__(self):
        return str(self.name)

    @property
    def profit_percent(self):
        return 100 * self.profit / self.deposit

    @property
    def yesterday_profit(self):
        try:
            accrual: UserProgramAccrual = self.accruals.get(created_at=now().date())
        except UserProgramAccrual.DoesNotExist:
            return None
        return accrual.amount

    @property
    def yesterday_profit_percent(self):
        yesterday = now().date() - timedelta(days=1)
        try:
            accrual: UserProgramAccrual = self.accruals.get(created_at=yesterday)
        except UserProgramAccrual.DoesNotExist:
            return None
        return accrual.percent_amount

    def _set_name(self):
        if not self.name:
            count = UserProgram.objects.filter(
                wallet=self.wallet, program=self.program
            ).count()
            if count == 0:
                self.name == self.program.name
            else:
                self.name = self.program.name + f"/{count + 1}"

    def _set_start_date(self):
        if not self.start_date:
            self.start_date = add_business_days(3)

    def _set_end_date(self):
        if not self.end_date and (duration := self.program.duration):
            self.end_date = self.start_date + relativedelta(months=duration)

    def _update_funds(self):
        if self.end_date:
            self.funds = self.deposit + self.profit
        else:
            self.funds = self.deposit + min(self.profit, 0)

    def start(self):
        self.status = self.Status.RUNNING
        self.save()

    def close(self):
        self.status = self.Status.FINISHED
        self.close_date = now().date()
        self.save()

    def update_deposit(self, amount):
        self.deposit += amount
        self.save()

    def update_profit(self, amount):
        self.profit += amount
        self.save()


class UserProgramHistory(models.Model):
    user_program = models.ForeignKey(
        UserProgram, on_delete=models.CASCADE, related_name="user_program_history"
    )
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(
        "Статус", choices=UserProgram.Status.choices, default=UserProgram.Status.INITIAL
    )
    deposit = models.DecimalField("Депозит", **decimal_usdt, default=Decimal("0.0"))
    funds = models.DecimalField(
        "Торговые средства", **decimal_usdt, default=Decimal("0.0")
    )
    profit = models.DecimalField(
        "Суммарный доход", **decimal_usdt, default=Decimal("0.0")
    )

    class Meta:
        unique_together = ("user_program", "created_at")
        verbose_name = "История программы пользователя"
        verbose_name_plural = "Истории программ пользователя"


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
    amount = models.DecimalField("Сумма", **decimal_usdt)
    status = models.CharField("Статус", choices=Status.choices, default=Status.INITIAL)
    created_at = models.DateField(
        verbose_name="Дата создания вывода",
        default=timezone.now,  # для парсинга внешней базы
    )
    apply_date = models.DateField("Дата зачисления на счет программы", **blank_and_null)
    done = models.BooleanField(default=False)

    def __str__(self):
        return f"Пополнение {self.program.name}"

    class Meta:
        verbose_name = "Пополнение"
        verbose_name_plural = "Пополнения программ"

    def decrease(self, amount):
        self.amount -= amount
        self.save()

    def cancel(self):
        self.status = self.Status.CANCELED
        self.save()

    def apply(self):
        self.program.update_deposit(amount=self.amount)
        OperationHistory.objects.create(
            wallet=self.program.wallet,
            type=OperationHistory.Type.TRANSFER_BETWEEN,
            description=dict(
                ru=f"Программа {self.program.name} пополнена",
                en=f"Program {self.program.name} has been replenished",
                cn=None,
            ),
            target_name=self.program.name,
            amount=self.amount,
        )
        self.apply_date = now().date()
        self.done = True
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
    percent_amount = models.DecimalField(
        "Сумма начисления в процентах от депозита", **decimal_pct
    )
    success_fee = models.DecimalField("Сумма Success Fee", **decimal_usdt)
    management_fee = models.DecimalField("Сумма Management Fee", **decimal_usdt)
    created_at = models.DateField("Дата")

    def __str__(self):
        return f"Начисление по {self.program.name}"

    class Meta:
        verbose_name = "Начисление"
        verbose_name_plural = "Начисления по программам"
        constraints = [
            models.UniqueConstraint(
                fields=["program", "created_at"],
                name="unique_program_accrual_created_at",
            )
        ]
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        if self.created_at is None:
            self.created_at = now().date()
        super().save(*args, **kwargs)
