from rest_framework.serializers import ModelSerializer

from apps.gdw_site.models import FundMonthlyStats


class FundTotalStatsSerializer(ModelSerializer):
    class Meta:
        model = FundMonthlyStats
        fields = ["date", "total"]
