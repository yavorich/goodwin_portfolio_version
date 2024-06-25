from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from apps.gdw_site.serializers import SiteProgramSerializer
from apps.gdw_site.models import SiteProgram


class SiteProgramsAPIView(ListAPIView):
    queryset = SiteProgram.objects.all()
    permission_classes = [AllowAny]
    serializer_class = SiteProgramSerializer
