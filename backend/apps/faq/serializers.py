from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from apps.faq.models import Answer


class AnswerSerializer(ModelSerializer):
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
        if obj.image:
            return self.context["request"].build_absolute_uri(obj.image.url)
        elif obj.video:
            return obj.video
