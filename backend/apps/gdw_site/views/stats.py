from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.gdw_site.models import FundDailyStats
from apps.gdw_site.serializers import FundTotalStatsSerializer


class FundStatsAPIView(ListAPIView):
    serializer_class = FundTotalStatsSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = FundDailyStats.objects.all()
        query_params = self.request.query_params
        start_date = query_params.get("start_date", queryset.earliest("date").date)
        end_date = query_params.get("end_date", queryset.latest("date").date)
        return queryset.filter(date__gte=start_date, date__lte=end_date)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        queryset = self.get_queryset()
        total_for_period = (
            queryset.latest("date").total - queryset.earliest("date").total
        )
        return Response(
            data={"total_for_period": total_for_period, "results": response.data}
        )
