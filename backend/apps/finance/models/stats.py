from django.db.models import Model, CharField, TextChoices, F, Sum, Q
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now, timedelta

from apps.finance.models import (
    WalletHistory,
    UserProgramHistory,
    WithdrawalRequest,
    Operation,
    UserProgramAccrual,
    UserProgram,
    UserProgramReplenishment,
)
from apps.accounts.models import Partner, UserCountHistory


class Stats(Model):
    class Name(TextChoices):
        WALLET = "wallet", _("Сумма в кошельках")
        ST_1 = "st_1", _("Сумма в программах ST-1")
        ST_2 = "st_2", _("Сумма в программах ST-2")
        ST_3 = "st_3", _("Сумма в программах ST-3")
        TO_WITHDRAW = "to_withdraw", _("Поставлено на вывод (ожидает рассмотрения)")
        TO_START = "to_start", _("Ожидает запуска")
        TO_REPLENISH = "to_replenish", _("Ожидает пополнения")
        TOTAL_FUND_BALANCE = "total_fund_balance", _("ИТОГО БАЛАНС ФОНДА")
        BRANCH_RU = "branch_ru", _("Доход филиала Россия")
        BRANCH_CN = "branch_cn", _("Доход филиала Китай")
        BRANCH_US = "branch_us", _("Доход филиала США")
        NET_PROFIT = "net_profit", _("Начисленная прибыль (чистая)")
        GROSS_PROFIT = "gross_profit", _("Начисленная прибыль (базовая)")
        SUCCESS_FEE = "success_fee", _("Удержано Success Fee")
        SUCCESS_FEE_NET = "success_fee_net", _(
            "Удержано Success Fee после вычета дохода Филиала"
        )
        EXTRA_FEE = "extra_fee", _("Удержано Extra Fee")
        MANAGEMENT_FEE = "management_fee", _("Удержано Management Fee")
        USERS_TOTAL = "users_total", _("Кол-во зарегистрированных пользователей")
        USERS_ACTIVE = "users_active", _("Кол-во активных пользователей")

    name = CharField("Показатель", choices=Name.choices, unique=True)

    # today = FloatField("Сегодня")
    # this_month = FloatField("В текущем месяце")
    # last_month = FloatField("В прошлом месяце")
    # two_months_ago = FloatField("В позапрошлом месяце")

    class Meta:
        verbose_name = "Показатель"
        verbose_name_plural = "Баланс фонда (статистика)"

    @property
    def today(self):
        today_date = now().date()
        return self.get_sum(today_date, today_date)

    @property
    def this_month(self):
        today_date = now().date()
        return self.get_sum(today_date)

    @property
    def last_month(self):
        end_of_last_month = now().date().replace(day=1) - timedelta(days=1)
        return self.get_sum(end_of_last_month)

    @property
    def two_months_ago(self):
        end_of_last_month = now().date().replace(day=1) - timedelta(days=1)
        end_two_months_ago = end_of_last_month.replace(day=1) - timedelta(days=1)
        return self.get_sum(end_two_months_ago)

    def get_sum(self, date, start_date=None):
        if self.name == self.Name.WALLET:
            return self.sum_wallet(date)
        if ("st_" in self.name) or ("users" in self.name):
            return getattr(self, f"sum_{self.name}")(date)

        start_date = start_date or date.replace(day=1)
        return getattr(self, f"sum_{self.name}")(start_date, date)

    def sum_wallet(self, date):
        return (
            WalletHistory.objects.filter(created_at=date).aggregate(
                total=Sum(F("free") + F("frozen"))
            )["total"]
            or 0
        )

    def sum_st_1(self, date):
        return self.sum_st(date, "ST-1")

    def sum_st_2(self, date):
        return self.sum_st(date, "ST-2")

    def sum_st_3(self, date):
        return self.sum_st(date, "ST-3")

    def sum_st(self, date, program_name):
        return (
            UserProgramHistory.objects.filter(
                user_program__program__name=program_name,
                created_at=date,
                status=UserProgram.Status.RUNNING,
            ).aggregate(total=Sum("deposit"))["total"]
            or 0
        )

    def sum_to_withdraw(self, start_date, end_date):
        return (
            WithdrawalRequest.objects.filter(
                created_at__lte=end_date,
                status=WithdrawalRequest.Status.PENDING,
            ).aggregate(total=Sum("original_amount"))["total"]
            or 0
        )

    def sum_to_start(self, start_date, end_date):
        return (
            UserProgram.objects.filter(
                created_at__date__lte=end_date,
                status=UserProgram.Status.INITIAL,
            ).aggregate(total=Sum("deposit"))["total"]
            or 0
        )

    def sum_to_replenish(self, start_date, end_date):
        return (
            UserProgramReplenishment.objects.filter(
                created_at__lte=end_date,
                status=UserProgramReplenishment.Status.INITIAL,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

    def sum_branch_ru(self, start_date, end_date):
        return self.sum_branch(start_date, end_date, region_name="Russia")

    def sum_branch_cn(self, start_date, end_date):
        return self.sum_branch(start_date, end_date, region_name="China")

    def sum_branch_us(self, start_date, end_date):
        return self.sum_branch(start_date, end_date, region_name="USA")

    def sum_branch(self, start_date, end_date, region_name):
        partner_profiles = Partner.objects.filter(region__name=region_name)
        user_programs = UserProgram.objects.filter(
            Q(wallet__user__partner__in=partner_profiles)
            | Q(wallet__user__partner_profile__in=partner_profiles)
        )
        accruals = UserProgramAccrual.objects.filter(
            program__in=user_programs,
            created_at__gte=start_date,
            created_at__lte=end_date,
        )
        query = Sum(
            F("success_fee")
            * Coalesce(
                F("program__wallet__user__partner__partner_fee"),
                F("program__wallet__user__partner_profile__partner_fee"),
            )
        )
        total_partner_fee = (
            accruals.aggregate(total_partner_fee=query)["total_partner_fee"] or 0
        )
        return total_partner_fee

    def sum_net_profit(self, start_date, end_date):
        query = Sum("amount")
        return self.sum_accrual(start_date, end_date, query)

    def sum_gross_profit(self, start_date, end_date):
        query = Sum(F("amount") + F("success_fee") + F("management_fee"))
        return self.sum_accrual(start_date, end_date, query)

    def sum_success_fee(self, start_date, end_date):
        query = Sum("success_fee")
        return self.sum_accrual(start_date, end_date, query)

    def sum_success_fee_net(self, start_date, end_date):
        query = Sum(
            F("success_fee")
            * (
                1
                - Coalesce(
                    F("program__wallet__user__partner__partner_fee"),
                    F("program__wallet__user__partner_profile__partner_fee"),
                )
            )
        )
        return self.sum_accrual(start_date, end_date, query)

    def sum_extra_fee(self, start_date, end_date):
        total = (
            Operation.objects.filter(
                type=Operation.Type.EXTRA_FEE,
                created_at__gte=start_date,
                created_at__lte=end_date,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        return total

    def sum_management_fee(self, start_date, end_date):
        query = Sum("management_fee")
        return self.sum_accrual(start_date, end_date, query)

    def sum_users_total(self, date):
        history = UserCountHistory.objects.filter(created_at=date).first()
        return getattr(history, "total", 0)

    def sum_users_active(self, date):
        history = UserCountHistory.objects.filter(created_at=date).first()
        return getattr(history, "active", 0)

    def sum_accrual(self, start_date, end_date, query):
        total = (
            UserProgramAccrual.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date,
            ).aggregate(total=query)["total"]
            or 0
        )
        return total

    def sum_total_fund_balance(self, start_date, end_date):
        return (
            self.sum_wallet(end_date)
            + self.sum_st_1(end_date)
            + self.sum_st_2(end_date)
            + self.sum_st_3(end_date)
            + self.sum_to_start(start_date, end_date)
            + self.sum_to_replenish(start_date, end_date)
            + self.sum_to_withdraw(start_date, end_date)
        )
