from rest_framework.fields import DecimalField, DateField, FloatField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.accounts.models import Region
from apps.accounts.models.user import Partner, User
from core.utils import decimal_usdt


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
    total_partner_fee = FloatField()


class InvestorsSerializer(ModelSerializer):
    total_funds = FloatField()
    total_net_profit = FloatField()

    class Meta:
        model = User
        fields = ["id", "full_name", "total_funds", "total_net_profit"]
        read_only_fields = fields


class PartnerInvestmentGraphSerializer(Serializer):
    created_at = DateField()
    total_sum = FloatField()
