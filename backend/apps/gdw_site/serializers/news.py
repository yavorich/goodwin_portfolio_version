from rest_framework.serializers import ModelSerializer

from apps.gdw_site.models import SiteNews


class SiteNewsSerializer(ModelSerializer):
    class Meta:
        model = SiteNews
        fields = ["id", "image", "title", "text", "tag", "date"]
