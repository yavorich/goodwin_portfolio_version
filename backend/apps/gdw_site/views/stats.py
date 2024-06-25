from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from apps.gdw_site.models import FundTotalStats
from apps.gdw_site.serializers import FundTotalStatsSerializer


class FundStatsAPIView(ListAPIView):
    queryset = FundTotalStats.objects.all()
    serializer_class = FundTotalStatsSerializer
    permission_classes = [AllowAny]
