from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from django.utils.translation import get_language

from apps.gdw_site.models.news import NEWS_MODELS
from apps.gdw_site.serializers import SiteNewsSerializer

from core.pagination import PageNumberSetPagination


class SiteNewsViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = SiteNewsSerializer
    pagination_class = PageNumberSetPagination

    def get_queryset(self):
        model = NEWS_MODELS[get_language()]
        return model.objects.filter(show_on_site=True).order_by("-date")
