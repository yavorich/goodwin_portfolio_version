from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from apps.gdw_site.models import RedirectLinks
from apps.gdw_site.serializers import RedirectLinkSerializer


class RedirectLinksAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = RedirectLinkSerializer

    def get_queryset(self):
        return RedirectLinks.objects.all()
