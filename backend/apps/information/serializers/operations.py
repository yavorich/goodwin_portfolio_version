from rest_framework.serializers import (
    ModelSerializer,
)
from rest_framework.exceptions import ValidationError

from apps.information.models import Operation, Wallet


class OperationSerializer(ModelSerializer):

    class Meta:
        model = Operation
        fields = [
            "id",
            "type",
            "amount",
            "created_at",
            "program",
        ]


class OperationCreateSerializer(ModelSerializer):

    class Meta:
        model = Operation
        fields = [
            "id",
            "type",
            "wallet",
            "program",
            "amount_free",
            "amount_frozen",
            "confirmed",
        ]

    def validate(self, attrs):
        wallet: Wallet = attrs["wallet"]
        program = attrs.get("program")
        _type: Operation.Type = attrs["type"]

        if not program and _type.startswith("program"):
            raise ValidationError(
                f"'program' field must be set for operation with type '{_type}"
            )

        types = Operation.Type
        if _type in [
            types.WITHDRAWAL,
            types.PROGRAM_START,
            types.PROGRAM_REPLENISHMENT,
            types.EXTRA_FEE,
        ]:
            if wallet.free < attrs["amount_free"]:
                raise ValidationError("Insufficient free funds.")
            if wallet.frozen < attrs["amount_frozen"]:
                raise ValidationError("Insufficient frozen funds.")

        if _type in [
            types.PROGRAM_ACCRUAL,
            types.PROGRAM_EARLY_CLOSURE,
            types.PROGRAM_REPLENISHMENT_CANCEL,
        ]:
            if program.funds < attrs["amount_free"]:
                raise ValidationError("Insufficient program funds.")

        return attrs

    def create(self, validated_data):
        return super().create(validated_data)
