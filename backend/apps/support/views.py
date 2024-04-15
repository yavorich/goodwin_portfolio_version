from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.support.models import Support
from apps.support.serializers import SupportContactSerializer


class ListSupportView(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Support.objects.exclude(link="")
    serializer_class = SupportContactSerializer
