from rest_framework.serializers import (
    ModelSerializer,
    FloatField,
)
from rest_framework.exceptions import ValidationError

from apps.information.models import Program, UserProgram, Wallet


class ProgramSerializer(ModelSerializer):
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


class UserProgramListSerializer(ModelSerializer):
    class Meta:
        model = UserProgram
        fields = [
            "id",
            "name",
            "start_date",
            "end_date",
            "funds",
        ]


class UserProgramCreateSerializer(ModelSerializer):
    amount_free = FloatField(write_only=True)
    amount_frozen = FloatField(write_only=True)

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
