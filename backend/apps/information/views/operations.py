from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from apps.information.models import Operation
from apps.information.serializers import OperationListSerializer


class OperationAPIView(ListAPIView):
    serializer_class = OperationListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["type"]

    def get_queryset(self):
        return Operation.objects.filter(user=self.request.user)

    def filter_queryset(self, queryset):
        _type = self.request.query_params.get("type")
        if _type and _type not in Operation.Type:
            available_types = [e.value for e in Operation.Type]
            raise ValidationError(
                f"Incorrect type='{_type}'. Must be one of {available_types}"
            )
        return super().filter_queryset(queryset)
