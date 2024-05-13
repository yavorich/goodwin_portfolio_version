from rest_framework.serializers import (
    ModelSerializer,
    DecimalField,
    FloatField,
    CharField,
    SerializerMethodField,
)
from rest_framework.exceptions import ValidationError

from apps.finance.models import (
    Program,
    UserProgram,
    Wallet,
    UserProgramReplenishment,
)
from apps.finance.services import get_wallet_settings_attr
from core.utils import decimal_usdt


class ProgramSerializer(ModelSerializer):
    min_deposit = FloatField()
    success_fee = SerializerMethodField()
    management_fee = SerializerMethodField()
    withdrawal_terms = SerializerMethodField()
    accrual_type = CharField(source="get_accrual_type_display")
    withdrawal_type = CharField(source="get_withdrawal_type_display")

    class Meta:
        model = Program
        fields = [
            "id",
            "name",
            "duration",
            "exp_profit",
            "max_risk",
            "min_deposit",
            "accrual_type",
            "withdrawal_type",
            "max_risk",
            "success_fee",
            "management_fee",
            "withdrawal_terms",
        ]

    def get_success_fee(self, obj: Program):
        wallet = self.context["wallet"]
        return float(get_wallet_settings_attr(wallet, "success_fee"))

    def get_management_fee(self, obj: Program):
        wallet = self.context["wallet"]
        return float(get_wallet_settings_attr(wallet, "management_fee"))

    def get_withdrawal_terms(self, obj: Program):
        wallet = self.context["wallet"]
        return int(get_wallet_settings_attr(wallet, "defrost_days"))


class UserProgramSerializer(ModelSerializer):
    class Meta:
        model = UserProgram
        fields = [
            "id",
            "name",
            "start_date",
            "end_date",
            "deposit",
            "profit",
            "profit_percent",
            "yesterday_profit",
            "yesterday_profit_percent",
        ]


class UserProgramCreateSerializer(ModelSerializer):
    amount_free = DecimalField(**decimal_usdt, write_only=True)
    amount_frozen = DecimalField(**decimal_usdt, write_only=True)

    class Meta:
        model = UserProgram
        fields = [
            "amount_free",
            "amount_frozen",
            "wallet",
            "program",
        ]

    def validate(self, attrs):
        wallet = Wallet.objects.get(pk=attrs["wallet"])
        if wallet.free < attrs["amount_free"]:
            raise ValidationError("Insufficient free funds.")
        if wallet.frozen < attrs["amount_frozen"]:
            raise ValidationError("Insufficient frozen funds.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("amount_free")
        validated_data.pop("amount_frozen")
        return super().create(validated_data)


class UserProgramReplenishmentSerializer(ModelSerializer):
    program = UserProgramSerializer()

    class Meta:
        model = UserProgramReplenishment
        fields = [
            "id",
            "program",
            "amount",
            "apply_date",
        ]
