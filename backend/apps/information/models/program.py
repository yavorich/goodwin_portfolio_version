from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now, timedelta

from core.utils import blank_and_null, add_business_days
from apps.accounts.models import User


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
    withdrawal_term = models.DurationField(_("Withdrawal term"))


class UserProgram(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running"
        START = "start"
        REPLENISHMENT = "replenishment"

    user = models.ForeignKey(User, related_name="programs", on_delete=models.CASCADE)
    program = models.ForeignKey(Program, related_name="users", on_delete=models.CASCADE)
    start_date = models.DateField(default=add_business_days(3))
    funds = models.FloatField(_("Underlying funds"))

    @property
    def name(self):
        count = self.objects.filter(user=self.user, program=self.program).count()
        return self.program.name + f"/{count}"

    @property
    def end_date(self):
        duration = self.program.duration
        if duration:
            return self.start_date + timedelta(months=duration)

    @property
    def status(self):
        if now().date() < self.start_date:
            return self.Status.START
        return self.Status.RUNNING  # добавить условие для replenishment
