from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.utils import blank_and_null, add_business_days, decimal_usdt, decimal_pct


class Program(models.Model):
    class AccrualType(models.TextChoices):
        DAILY = "daily", _("Daily")

    class WithdrawalType(models.TextChoices):
        DAILY = "daily", _("Daily")
        AFTER_FINISH = "after_end", _("After end")

    name = models.CharField(_("Program name"), max_length=31)
    duration = models.IntegerField(_("Duration (months)"), **blank_and_null)
    exp_profit = models.DecimalField(_("Expected profit"), **decimal_pct)
    min_deposit = models.DecimalField(_("Minimum deposit"), **decimal_usdt)
    accrual_type = models.CharField(_("Accrual type"), choices=AccrualType.choices)
    withdrawal_type = models.CharField(
        _("Withdrawal type"), choices=WithdrawalType.choices
    )
    max_risk = models.FloatField(_("Maximum risk"))
    success_fee = models.DecimalField("Success fee", **decimal_pct)
    management_fee = models.DecimalField("Management fee", **decimal_pct)
    withdrawal_terms = models.IntegerField(_("Withdrawal term (days)"))


class ProgramResult(models.Model):
    program = models.ForeignKey(
        Program, related_name="results", on_delete=models.CASCADE, **blank_and_null
    )
    result = models.DecimalField(**decimal_pct, default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = "created_at"
        ordering = ["-created_at"]


class UserProgram(models.Model):
    class Status(models.TextChoices):
        INITIAL = "initial", "Ожидает запуска"
        RUNNING = "running", "Запущена"
        FINISHED = "finished", "Завершена"

    name = models.CharField(max_length=31, **blank_and_null)
    wallet = models.ForeignKey(
        "Wallet", related_name="programs", on_delete=models.CASCADE
    )
    program = models.ForeignKey(Program, related_name="users", on_delete=models.CASCADE)
    start_date = models.DateField(**blank_and_null)
    end_date = models.DateField(**blank_and_null)
    status = models.CharField(choices=Status.choices, default=Status.INITIAL)
    deposit = models.DecimalField(
        _("Underlying funds"), **decimal_usdt, **blank_and_null
    )
    funds = models.DecimalField(_("Underlying funds"), **decimal_usdt, default=0.0)
    force_closed = models.BooleanField(default=False)

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
        UserProgram, related_name="replenishments", on_delete=models.CASCADE
    )
    operation = models.OneToOneField(
        "Operation", on_delete=models.CASCADE, **blank_and_null
    )
    amount = models.DecimalField(**decimal_usdt)
    status = models.CharField(choices=Status.choices, default=Status.INITIAL)
    apply_date = models.DateField(**blank_and_null)

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
        UserProgram, related_name="accruals", on_delete=models.CASCADE
    )
    amount = models.DecimalField(**decimal_usdt)
    success_fee = models.DecimalField(**decimal_usdt)
    created_at = models.DateField(auto_now_add=True)
