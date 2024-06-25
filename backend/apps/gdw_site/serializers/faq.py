from rest_framework.serializers import ModelSerializer, CharField

from apps.gdw_site.models import SiteAnswer


class SiteAnswerSerializer(ModelSerializer):
    title = CharField()
    text = CharField()

    class Meta:
        model = SiteAnswer
        fields = ["title", "text"]
