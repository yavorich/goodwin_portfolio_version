from rest_framework.serializers import ModelSerializer, CharField, SerializerMethodField

from apps.gdw_site.models import SiteNewsRus
from core.serializers import HttpsFileField


class SiteNewsSerializer(ModelSerializer):
    tag = CharField(source="tag.tag", allow_null=True)
    image = HttpsFileField()
    date = SerializerMethodField()

    class Meta:
        model = SiteNewsRus
        fields = ["id", "image", "title", "text", "tag", "date"]

    def get_date(self, obj: SiteNewsRus):
        return obj.date.strftime("%d.%m.%Y")
