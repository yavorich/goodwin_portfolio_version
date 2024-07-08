from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny

from apps.gdw_site.models import SocialContact
from apps.gdw_site.serializers import SocialContactSerializer


class SocialContactsViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = SocialContactSerializer

    def get_queryset(self):
        return SocialContact.objects.exclude(link="")
