from rest_framework.fields import DateField, FloatField
from rest_framework.serializers import Serializer


class TotalProfitStatisticsGraphSerializer(Serializer):
    created_at = DateField()
    amount = FloatField()
    total_amount = FloatField()
