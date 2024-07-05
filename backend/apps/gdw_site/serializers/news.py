from rest_framework.serializers import ModelSerializer, CharField

from apps.gdw_site.models import SiteNews
from core.serializers import HttpsFileField


class SiteNewsSerializer(ModelSerializer):
    tag = CharField(source="tag.tag")
    image = HttpsFileField()

    class Meta:
        model = SiteNews
        fields = ["id", "image", "title", "text", "tag", "date"]
