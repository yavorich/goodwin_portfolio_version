import pandas as pd
from rest_framework.fields import (
    FloatField,
    DateField,
    IntegerField,
    CharField,
    SerializerMethodField,
)
from rest_framework.serializers import ModelSerializer, Serializer

from apps.information.models import UserProgramAccrual


class TotalProfitStatisticsGraphSerializer(ModelSerializer):
    amount = FloatField()
    percent_amount = FloatField()
    percent_total_amount = FloatField()

    class Meta:
        model = UserProgramAccrual
        fields = [
            "created_at",
            "amount",
            "percent_amount",
            "percent_total_amount",
        ]


class GeneralInvestmentStatisticsSerializer(Serializer):
    total_funds = FloatField()
    total_profits = FloatField()
    start_date = DateField()


class TableStatisticsSerializer(Serializer):
    day_of_week = IntegerField()
    day_of_week_verbose = SerializerMethodField()
    created_at = DateField()
    trading_day = SerializerMethodField()
    funds = FloatField()
    amount = FloatField()
    percent_amount = FloatField()
    percent_total_amount = FloatField()
    profitability = FloatField()
    success_fee = FloatField()
    management_fee = FloatField()
    replenishment = FloatField()
    withdrawal = FloatField()
    status = CharField()

    def get_trading_day(self, obj):
        holidays = self.context.get("holidays")

        if (
            obj["created_at"].weekday() >= 5
            or pd.Timestamp(obj["created_at"]) in holidays
        ):
            return None

        return len(
            pd.bdate_range(
                obj["created_at"].replace(day=1),
                obj["created_at"],
                freq="C",
                holidays=holidays,
            ),
        )

    def get_day_of_week_verbose(self, obj):
        week_days_list = self.context.get("week_days_list")
        return week_days_list[obj["day_of_week"] - 1].encode("utf-8")
