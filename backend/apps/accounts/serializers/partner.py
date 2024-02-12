from rest_framework.fields import DecimalField, FloatField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.accounts.models import Region
from apps.accounts.models.user import Partner


class RegionSerializer(ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "name"]


class PartnerSerializer(ModelSerializer):
    region = RegionSerializer()

    class Meta:
        model = Partner
        fields = ["id", "partner_id", "region", "partner_fee"]


class PartnerRetrieveSerializer(PartnerSerializer):
    class Meta(PartnerSerializer.Meta):
        fields = ["partner_id", "region"]


class PartnerTotalFeeSerializer(Serializer):
    total_success_fee = FloatField()
    total_partner_fee = DecimalField(max_digits=3, decimal_places=2)


# class PartnerGeneralStatisticsSerializer(ModelSerializer):
