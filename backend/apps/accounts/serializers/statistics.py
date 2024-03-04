from rest_framework.fields import FloatField, DateField
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
