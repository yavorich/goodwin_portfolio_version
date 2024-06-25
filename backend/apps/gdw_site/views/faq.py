from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from apps.gdw_site.models import SiteAnswer
from apps.gdw_site.serializers import SiteAnswerSerializer


class SiteAnswerAPIView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = SiteAnswer.objects.order_by("title")
    serializer_class = SiteAnswerSerializer
