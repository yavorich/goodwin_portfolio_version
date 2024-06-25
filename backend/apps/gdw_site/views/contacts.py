from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.gdw_site.models import SiteContact
from apps.gdw_site.serializers import SiteContactsSerializer


class SiteContactsAPIView(ListAPIView):
    queryset = SiteContact.objects.all()
    serializer_class = SiteContactsSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(data=response.data[0])
