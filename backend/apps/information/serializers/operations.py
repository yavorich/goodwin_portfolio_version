import requests
from rest_framework.fields import DecimalField
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    BooleanField,
    Serializer,
)
from rest_framework.exceptions import ValidationError

from apps.information.models import Operation, Action
from config import settings
from core.utils import decimal_usdt


class OperationSerializer(ModelSerializer):
    operation_type = CharField(source="operation.get_type_display")
    action_type = CharField(source="get_type_display")

    class Meta:
        model = Action
        fields = [
            "id",
            "operation_type",
            "action_type",
            "name",
            "target_name",
            "created_at",
            "amount",
        ]


class OperationCreateSerializer(ModelSerializer):
    confirmed = BooleanField(read_only=True)
    operation_type = None

    class Meta:
        model = Operation
        fields = [
            "id",
            "wallet",
            "confirmed",
        ]

    def _validate_wallet(self, attrs, free=None, frozen=None):
        free = free or attrs.get("amount_free")
        frozen = frozen or attrs.get("amount_frozen")
        if free and attrs["wallet"].free < free:
            raise ValidationError("Insufficient free funds.")
        if frozen and attrs["wallet"].frozen < frozen:
            raise ValidationError("Insufficient frozen funds.")

    def create(self, validated_data):
        validated_data["type"] = self.operation_type
        return super().create(validated_data)


class ProgramStartSerializer(OperationCreateSerializer):
    operation_type = Operation.Type.PROGRAM_START

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + [
            "program",
            "amount_free",
            "amount_frozen",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def validate(self, attrs):
        self._validate_wallet(attrs)
        if attrs["amount_free"] + attrs["amount_frozen"] < attrs["program"].min_deposit:
            raise ValidationError(
                f"Minimum program deposit = {attrs['program'].min_deposit}"
            )
        return attrs


class ProgramReplenishmentSerializer(OperationCreateSerializer):
    operation_type = Operation.Type.PROGRAM_REPLENISHMENT

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + [
            "user_program",
            "amount_free",
            "amount_frozen",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def validate(self, attrs):
        self._validate_wallet(attrs)
        if attrs["amount_free"] + attrs["amount_frozen"] < 100:
            raise ValidationError(f"Minimum program replenishment = {100}")
        return attrs


class ProgramReplenishmentCancelSerializer(OperationCreateSerializer):
    operation_type = Operation.Type.PROGRAM_REPLENISHMENT_CANCEL

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + [
            "replenishment",
            "amount",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def validate(self, attrs):
        remainder = attrs["replenishment"].amount - attrs["amount"]
        if 0 < remainder < 100:
            raise ValidationError(
                "Minimum replenishment amount after cancellation - 100 USDT"
            )
        if remainder < 0:
            raise ValidationError("Insufficient funds to cancel")
        return attrs

    def create(self, validated_data):
        validated_data["partial"] = (
            validated_data["replenishment"].amount != validated_data["amount"]
        )
        return super().create(validated_data)


class ProgramClosureSerializer(OperationCreateSerializer):
    operation_type = Operation.Type.PROGRAM_CLOSURE
    early_closure = BooleanField(default=True)

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + [
            "user_program",
            "amount",
            "early_closure",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def validate(self, attrs):
        min_deposit = attrs["user_program"].program.min_deposit
        remainder = attrs["user_program"].deposit - attrs["amount"]
        if 0 < remainder < min_deposit:
            raise ValidationError(
                f"Minimum program deposit after cancellation - {min_deposit} USDT"
            )
        if remainder < 0:
            raise ValidationError("Insufficient program deposit")
        return attrs

    def create(self, validated_data):
        validated_data["partial"] = (
            validated_data["user_program"].deposit != validated_data["amount"]
        )
        return super().create(validated_data)


class WalletDefrostSerializer(OperationCreateSerializer):
    operation_type = Operation.Type.DEFROST

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + [
            "amount",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def validate(self, attrs):
        self._validate_wallet(attrs, frozen=attrs["amount"])
        return attrs


class WalletTransferSerializer(OperationCreateSerializer):
    operation_type = Operation.Type.TRANSFER

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + [
            "receiver",
            "amount_free",
            "amount_frozen",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def validate(self, attrs):
        self._validate_wallet(attrs)
        return attrs

    def create(self, validated_data: dict):
        return super().create(validated_data)


class WalletReplenishmentSerializer(OperationCreateSerializer):
    operation_type = Operation.Type.REPLENISHMENT

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + ["amount"]
        extra_kwargs = {f: {"required": True} for f in fields}

    def create(self, validated_data):
        operation: Operation = super().create(validated_data)
        hook = f"http://{settings.NODE_JS_HOST}/{settings.NODE_JS_HOOK_URL}/"
        data = {"operationId": operation.uuid, "expectedAmount": operation.amount}
        result = requests.post(hook, data)
        if result.status_code != 201:
            operation.delete()
            raise ValidationError("Server is busy")
        return operation


class WalletWithdrawalSerializer(OperationCreateSerializer):
    operation_type = Operation.Type.WITHDRAWAL

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + []


class OperationReplenishmentConfirmSerializer(Serializer):
    amount = DecimalField(**decimal_usdt)


program_operations_serializers = {
    "start": ProgramStartSerializer,
    "replenish": ProgramReplenishmentSerializer,
    "cancel": ProgramReplenishmentCancelSerializer,
    "close": ProgramClosureSerializer,
}

wallet_operations_serializers = {
    "replenish": WalletReplenishmentSerializer,
    "withdraw": WalletWithdrawalSerializer,
    "transfer": WalletTransferSerializer,
    "defrost": WalletDefrostSerializer,
}
