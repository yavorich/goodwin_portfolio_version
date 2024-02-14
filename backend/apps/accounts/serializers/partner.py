from rest_framework.fields import DecimalField, DateField
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
    total_success_fee = DecimalField(max_digits=12, decimal_places=2)
    total_partner_fee = DecimalField(max_digits=12, decimal_places=2)


class InvestorsSerializer(ModelSerializer):
    total_funds = DecimalField(**decimal_usdt)
    total_net_profit = DecimalField(**decimal_usdt)

    class Meta:
        model = User
        fields = ["id", "full_name", "total_funds", "total_net_profit"]
        read_only_fields = fields


class PartnerInvestmentGraphSerializer(Serializer):
    date = DateField()
    total_amount = DecimalField(**decimal_usdt)
