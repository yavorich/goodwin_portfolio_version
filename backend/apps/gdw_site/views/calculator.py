from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.gdw_site.serializers import CalculatorSerializer, TopupPeriod


class CalculatorAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = CalculatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class TopupPeriodListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        data = [{"name": str(e), "verbose_name": e.label} for e in TopupPeriod]
        return Response(data=data)
