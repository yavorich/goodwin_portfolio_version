from rest_framework.serializers import ModelSerializer

from apps.gdw_site.models import FundDailyStats


class FundTotalStatsSerializer(ModelSerializer):

    class Meta:
        model = FundDailyStats
        fields = ["date", "percent", "total"]
