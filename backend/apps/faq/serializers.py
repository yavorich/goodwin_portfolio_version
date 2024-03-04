from django.conf import settings
from rest_framework.fields import SerializerMethodField, CharField
from rest_framework.serializers import ModelSerializer
from django.utils import translation

from apps.faq.models import Answer


class AnswerSerializer(ModelSerializer):
    title = CharField()
    text = CharField()
    enclosure = SerializerMethodField()

    class Meta:
        model = Answer
        fields = [
            "id",
            "title",
            "text",
            "enclosure",
        ]

    def get_enclosure(self, obj):
        language = translation.get_language() or settings.LANGUAGE_CODE
        if obj.image.get(language):
            uri = self.context["request"].build_absolute_uri(obj.image.url)
            return uri.replace("http:", "https:")
        elif obj.video.get(language):
            return obj.video.translate()
