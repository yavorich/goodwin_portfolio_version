from rest_framework.serializers import ModelSerializer, CharField

from apps.support.models import Support


class SupportContactSerializer(ModelSerializer):
    link = CharField(allow_null=True)

    class Meta:
        model = Support
        fields = ["service", "link"]
