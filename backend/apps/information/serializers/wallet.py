from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    IntegerField,
    EmailField,
    FloatField,
    Serializer,
)
from rest_framework.exceptions import ValidationError

from apps.information.models import Wallet, FrozenItem
from apps.accounts.models import User


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
            raise ValidationError("ID WALLET не существует")
        if user.email != attrs["email"]:
            raise ValidationError("Неверный email")
        return attrs

    def to_representation(self, instance):
        user = User.objects.get(**instance)
        return {"id": user.id, "full_name": user.full_name}
