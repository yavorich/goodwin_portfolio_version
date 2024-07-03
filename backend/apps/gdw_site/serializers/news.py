from rest_framework.serializers import ModelSerializer, CharField

from apps.gdw_site.models import SiteNews


class SiteNewsSerializer(ModelSerializer):
    tag = CharField(source="tag.tag")

    class Meta:
        model = SiteNews
        fields = ["id", "image", "title", "text", "tag", "date"]
