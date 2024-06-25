from rest_framework.serializers import ModelSerializer

from apps.gdw_site.models import SiteContact


class SiteContactsSerializer(ModelSerializer):
    class Meta:
        model = SiteContact
        fields = ["address", "certificate", "email", "latitude", "longitude"]
