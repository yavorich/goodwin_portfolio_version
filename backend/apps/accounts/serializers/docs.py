from django.conf import settings
from django.utils import translation
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from apps.accounts.models import Docs


class DocsSerializer(ModelSerializer):
    file = SerializerMethodField()

    class Meta:
        model = Docs
        fields = [
            "file",
        ]

    def get_file(self, obj):
        language = translation.get_language() or settings.LANGUAGE_CODE
        if obj.file.get(language):
            return self.context["request"].build_absolute_uri(obj.file.url)
