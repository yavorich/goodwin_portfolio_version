from rest_framework.serializers import ModelSerializer

from apps.information.models import Operation


class OperationListSerializer(ModelSerializer):
    class Meta:
        model = Operation
        fields = [
            "type",
            "amount",
            "created_at",
            "program",
        ]
