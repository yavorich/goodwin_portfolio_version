from rest_framework.serializers import (
    Serializer,
    IntegerField,
    DecimalField,
    DateField,
    CharField,
)
from rest_framework.exceptions import ValidationError
from django.db.models import TextChoices
from django.utils.timezone import timedelta
from django.utils.translation import gettext_lazy as _
from dateutil.relativedelta import relativedelta

from apps.gdw_site.models import SiteProgram, FundDailyStats
from apps.finance.services.wallet_settings_attr import get_wallet_settings_attr
from core.utils import decimal_usdt
from core.utils.error import get_error, ErrorMessageType


class TopupPeriod(TextChoices):
    MONTHLY = "monthly", _("Ежемесячно")
    TWO_MONTHS = "two_months", _("Раз в 2 месяца")
    QUARTER = "quarter", _("Раз в квартал")
    FOUR_MONTHS = "four_months", _("Раз в 4 месяца")
    HALF_YEAR = "half_year", _("Раз в полгода")


TOPUP_PERIOD_MONTHS = {
    TopupPeriod.MONTHLY: 1,
    TopupPeriod.TWO_MONTHS: 2,
    TopupPeriod.QUARTER: 3,
    TopupPeriod.FOUR_MONTHS: 4,
    TopupPeriod.HALF_YEAR: 6,
}


class CalculatorSerializer(Serializer):
    program = IntegerField()
    deposit = DecimalField(**decimal_usdt)
    start_date = DateField()
    end_date = DateField()
    topup = DecimalField(**decimal_usdt, required=False)
    topup_period = CharField(required=False)

    def validate_start_date(self, value):
        min_date = FundDailyStats.objects.first().date
        if value < min_date:
            raise ValidationError("Недостаточно данных за указанный период")
        return value

    def validate_end_date(self, value):
        max_date = FundDailyStats.objects.last().date
        if value > max_date:
            raise ValidationError("Недостаточно данных за указанный период")
        return value

    def validate(self, attrs):
        program = SiteProgram.objects.filter(pk=attrs["program"]).first()
        if months := program.duration:
            if attrs["end_date"] > attrs["start_date"] + relativedelta(months=months):
                raise ValidationError(
                    f"Выбранная программа длится не более {months} месяцев"
                )
        deposit = attrs["deposit"]
        if deposit < program.min_deposit:
            get_error(
                error_type=ErrorMessageType.MIN_PROGRAM_DEPOSIT,
                insertions={"amount": program.min_deposit},
            )
        if not program:
            raise ValidationError("Program not found")

        if attrs.get("topup") and not attrs.get("topup_period"):
            raise ValidationError("Missing value: topup_period")

        result, topups = calculate_program_result(attrs, program)
        result_percent = round(100 * result / (deposit + topups), 2)

        return {
            "deposit": attrs["deposit"],
            "topups": topups,
            "result": result,
            "result_percent": result_percent,
        }

    def validate_topup_period(self, value):
        if value is not None and value not in TopupPeriod:
            raise ValidationError("Wrong topup_period value")
        return value


def calculate_program_result(attrs, program: SiteProgram):
    current_date = attrs["start_date"]
    end_date = attrs["end_date"]
    deposit = attrs["deposit"]
    topup = attrs.get("topup", 0)
    if topup:
        topup_period = TOPUP_PERIOD_MONTHS[attrs["topup_period"]]
        topup_interval = relativedelta(months=topup_period) if topup_period else None
        next_topup_date = current_date + topup_interval

    success_fee_pct = get_wallet_settings_attr(None, "success_fee")
    management_fee_pct = get_wallet_settings_attr(None, "management_fee")

    result = 0
    topups = 0

    while current_date <= end_date:
        daily_profit_pct = FundDailyStats.objects.get(date=current_date).percent
        today_profit = deposit * daily_profit_pct / 100
        management_fee = deposit * management_fee_pct / 100
        success_fee = max(0, today_profit * success_fee_pct / 100)
        today_profit -= success_fee + management_fee
        result += today_profit
        if program.duration is not None:
            deposit += today_profit
        if topup and current_date == next_topup_date:
            topups += topup
            deposit += topup
            next_topup_date += topup_interval
        current_date += timedelta(days=1)
    return round(result, 2), round(topups, 2)
