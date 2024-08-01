from rest_framework.serializers import ModelSerializer, URLField

from apps.gdw_site.models import RedirectLinks


class RedirectLinkSerializer(ModelSerializer):
    url = URLField()

    class Meta:
        model = RedirectLinks
        fields = ["link_type", "url"]
