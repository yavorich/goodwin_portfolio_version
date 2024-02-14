from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    EmailField,
    BooleanField,
)
from rest_framework.exceptions import ValidationError

from apps.information.models import Operation, Action


class OperationSerializer(ModelSerializer):
    operation_type = CharField(source="operation.type")
    action_type = CharField(source="type")

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

    class Meta:
        model = Operation
        fields = [
            "id",
            "type",
            "wallet",
            "confirmed",
        ]

    def _validate_wallet(self, attrs):
        free = attrs.get("amount_free")
        frozen = attrs.get("amount_frozen")
        if free and attrs["wallet"].free < free:
            raise ValidationError("Insufficient free funds.")
        if frozen and attrs["wallet"].frozen < frozen:
            raise ValidationError("Insufficient frozen funds.")


class ProgramStartSerializer(OperationCreateSerializer):
    type = CharField(default=Operation.Type.PROGRAM_START)

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
    type = CharField(default=Operation.Type.PROGRAM_REPLENISHMENT)

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
    type = CharField(default=Operation.Type.PROGRAM_REPLENISHMENT_CANCEL)

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + [
            "replenishment",
            "amount",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def validate(self, attrs):
        if 0 < attrs["replenishment"].amount - attrs["amount"] < 100:
            raise ValidationError(
                "Minimum replenishment amount after cancellation - 100 USDT"
            )
        return attrs


class ProgramClosureSerializer(OperationCreateSerializer):
    type = CharField(default=Operation.Type.PROGRAM_CLOSURE)

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + [
            "user_program",
            "amount",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def validate(self, attrs):
        min_deposit = attrs["user_program"].program.min_deposit
        if 0 < attrs["user_program"].funds - attrs["amount"] < min_deposit:
            raise ValidationError(
                f"Minimum program deposit after cancellation - {min_deposit} USDT"
            )
        return attrs


class WalletDefrostSerializer(OperationCreateSerializer):
    type = CharField(default=Operation.Type.DEFROST)

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + [
            "amount_frozen",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def validate(self, attrs):
        self._validate_wallet(attrs)


class WalletTransferSerializer(OperationCreateSerializer):
    email = EmailField(write_only=True)
    type = CharField(default=Operation.Type.TRANSFER)

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + [
            "receiver",
            "email",
            "amount_free",
            "amount_frozen",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def validate(self, attrs):
        self._validate_wallet(attrs)
        if attrs["email"] != attrs["receiver"].user.email:
            raise ValidationError("Email is incorrect")
        return attrs

    def create(self, validated_data: dict):
        validated_data.pop("email", None)
        return super().create(validated_data)


class WalletReplenishmentSerializer(OperationCreateSerializer):
    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + []


class WalletWithdrawalSerializer(OperationCreateSerializer):
    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + []


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
