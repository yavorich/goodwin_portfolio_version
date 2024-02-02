from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now, timedelta

from core.utils import blank_and_null, add_business_days


class Program(models.Model):
    class AccrualType(models.TextChoices):
        DAILY = "daily", _("Daily")
        AFTER_END = "after_end", _("After end")

    class WithdrawalType(models.TextChoices):
        DAILY = "daily", _("Daily")
        AFTER_END = "after_end", _("After end")

    name = models.CharField(_("Program name"), max_length=31)
    duration = models.IntegerField(_("Duration (months)"), **blank_and_null)
    exp_profit = models.FloatField(_("Expected profit"))
    min_deposit = models.FloatField(_("Minimum deposit"))
    accrual_type = models.CharField(_("Accrual type"), choices=AccrualType.choices)
    withdrawal_type = models.CharField(
        _("Withdrawal type"), choices=WithdrawalType.choices
    )
    max_risk = models.FloatField(_("Maximum risk"))
    success_fee = models.FloatField("Success fee")
    management_fee = models.FloatField("Management fee")
    withdrawal_terms = models.IntegerField(_("Withdrawal term (days)"))


class UserProgram(models.Model):
    class Status(models.TextChoices):
        INITIAL = "initial", "Ожидает запуска"
        RUNNING = "running", "Запущена"
        REPLENISHMENT = "replenishment", "Ожидает пополнения"
        EARLY_CLOSURE = "early_closure", "Завершена досрочно"
        FINISHED = "finished", "Завершена"

    name = models.CharField(max_length=31, **blank_and_null)
    wallet = models.ForeignKey(
        "Wallet", related_name="programs", on_delete=models.CASCADE
    )
    program = models.ForeignKey(Program, related_name="users", on_delete=models.CASCADE)
    start_date = models.DateField(default=add_business_days(3))
    funds = models.FloatField(_("Underlying funds"), default=0.0)
    force_closed = models.BooleanField(default=False)
    last_replenishment = models.DateTimeField(**blank_and_null)

    def __str__(self):
        return str(self.name)

    @property
    def end_date(self):
        duration = self.program.duration
        if duration:
            return self.start_date + timedelta(months=duration)

    @property
    def status(self):
        if self.force_closed:
            return self.Status.EARLY_CLOSURE
        if self.last_replenishment and now().date() < add_business_days(
            days=3, start=self.last_replenishment.date()
        ):
            return self.Status.REPLENISHMENT
        if now().date() < self.start_date:
            return self.Status.INITIAL
        if self.end_date and now().date() >= self.end_date:
            return self.Status.FINISHED
        return self.Status.RUNNING

    def save(self, *args, **kwargs):
        if not self.name:
            count = UserProgram.objects.filter(
                wallet=self.wallet, program=self.program
            ).count()
            self.name = self.program.name + f"/{count + 1}"
        super().save(*args, **kwargs)

    def update_balance(self, amount):
        self.funds += amount
        self.save()
