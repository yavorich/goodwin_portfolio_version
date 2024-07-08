from rest_framework.serializers import ModelSerializer, CharField

from apps.gdw_site.models import SocialContact


class SocialContactSerializer(ModelSerializer):
    service = CharField()
    link = CharField(allow_null=True)

    class Meta:
        model = SocialContact
        fields = ["id", "service", "link"]
