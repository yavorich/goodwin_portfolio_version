from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.support.models import Support
from apps.support.serializers import SupportContactSerializer


class ListSupportView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SupportContactSerializer

    def get_queryset(self):
        return Support.objects.exclude(link="")
