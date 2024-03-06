from rest_framework.fields import FloatField, DateField, IntegerField, CharField
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
    created_at = DateField()
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
