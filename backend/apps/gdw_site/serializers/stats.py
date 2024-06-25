from rest_framework.serializers import ModelSerializer

from apps.gdw_site.models import FundTotalStats


class FundTotalStatsSerializer(ModelSerializer):
    class Meta:
        model = FundTotalStats
        fields = ["date", "total"]
