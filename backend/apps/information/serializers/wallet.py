from rest_framework.serializers import ModelSerializer, SerializerMethodField

from apps.information.models import Wallet, FrozenItem


class WalletSerializer(ModelSerializer):
    total = SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ["total", "free", "frozen"]

    def get_total(self, obj: Wallet):
        return obj.free + obj.frozen


class FrozenItemSerializer(ModelSerializer):

    class Meta:
        model = FrozenItem
        fields = ["id", "amount", "frost_date", "defrost_date"]
