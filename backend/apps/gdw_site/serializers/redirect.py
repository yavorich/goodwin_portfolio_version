from rest_framework.serializers import ModelSerializer

from apps.gdw_site.models import RedirectLinks


class RedirectLinkSerializer(ModelSerializer):

    class Meta:
        model = RedirectLinks
        fields = ["link_type", "url"]
