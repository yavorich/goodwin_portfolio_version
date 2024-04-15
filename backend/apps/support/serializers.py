from rest_framework.serializers import ModelSerializer, CharField

from apps.support.models import Support
from core.serializers import HttpsFileField


class SupportContactSerializer(ModelSerializer):
    link = CharField(allow_null=True)
    logo = HttpsFileField()

    class Meta:
        model = Support
        fields = ["service", "logo", "link"]
