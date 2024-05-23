from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    IntegerField,
    EmailField,
    FloatField,
    Serializer,
)

from apps.finance.models import Wallet, FrozenItem, WalletSettings
from apps.accounts.models import User, ErrorType
from core.utils.error import get_error


class WalletSerializer(ModelSerializer):
    free = FloatField()
    frozen = FloatField()
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


class WalletTransferUserSerializer(Serializer):
    id = IntegerField(required=True)
    email = EmailField(required=True)

    def validate(self, attrs):
        try:
            user = User.objects.get(id=attrs["id"])
        except User.DoesNotExist:
            get_error(error_type=ErrorType.USER_NOT_FOUND)
        if user.email != attrs["email"]:
            get_error(error_type=ErrorType.USER_EMAIL_MISMATCH)
        if user == self.context["user"]:
            get_error(error_type=ErrorType.SELF_TRANSFER)
        return attrs

    def to_representation(self, instance):
        user = User.objects.get(**instance)
        return {"id": user.id, "full_name": f"{user.last_name} {user.first_name[0]}."}


class WalletSettingsSerializer(ModelSerializer):
    commission_on_replenish = FloatField()
    commission_on_withdraw = FloatField()
    commission_on_transfer = FloatField()
    extra_fee = FloatField()

    class Meta:
        model = WalletSettings
        fields = [
            "commission_on_replenish",
            "commission_on_withdraw",
            "commission_on_transfer",
            "extra_fee",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        default_settings = WalletSettings.objects.get(wallet__isnull=True)
        for key in data:
            if data.get(key) is None:
                data[key] = getattr(default_settings, key)
        return data
