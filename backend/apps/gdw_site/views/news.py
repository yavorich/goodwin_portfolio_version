from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny

from apps.gdw_site.models import SiteNews
from apps.gdw_site.serializers import SiteNewsSerializer

from core.pagination import PageNumberSetPagination


class SiteNewsViewSet(ReadOnlyModelViewSet):
    queryset = SiteNews.objects.filter(show_on_site=True)
    permission_classes = [AllowAny]
    serializer_class = SiteNewsSerializer
    pagination_class = PageNumberSetPagination
