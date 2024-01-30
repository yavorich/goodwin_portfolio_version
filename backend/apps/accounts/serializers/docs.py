from rest_framework.serializers import ModelSerializer

from apps.accounts.models import Docs


class DocsSerializer(ModelSerializer):
    class Meta:
        model = Docs
        fields = [
            "file",
        ]
