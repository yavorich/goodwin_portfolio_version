from rest_framework.fields import FloatField, DateField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.information.models import UserProgramAccrual


class TotalProfitStatisticsGraphSerializer(ModelSerializer):
    amount = FloatField()
    total_amount = FloatField()

    class Meta:
        model = UserProgramAccrual
        fields = ["created_at", "amount", "total_amount"]


class GeneralInvestmentStatisticsSerializer(Serializer):
    total_funds = FloatField()
    total_profits = FloatField()
    start_date = DateField()
