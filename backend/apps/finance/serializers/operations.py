import json
import requests

from django.utils.translation import gettext as _
from rest_framework.fields import DecimalField
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    BooleanField,
    Serializer,
    FloatField,
    # SerializerMethodField,
)
from rest_framework.exceptions import ValidationError

from apps.finance.models import (
    Operation,
    OperationHistory,
    OperationConfirmation,
)
from config import settings
from core.exceptions import ServiceUnavailable
from core.utils import decimal_usdt


class OperationHistorySerializer(ModelSerializer):
    type = CharField(source="get_type_display")
    description = CharField()
    amount = FloatField()

    class Meta:
        model = OperationHistory
        fields = [
            "id",
            "type",
            "operation_type",
            "description",
            "target_name",
            "created_at",
            "amount",
        ]

    # def get_operation_type(self, obj: OperationHistory):
    #     if obj.operation:
    #         return obj.operation.get_type_display()
    #     return None


class OperationCreateSerializer(ModelSerializer):
    operation_type = None

    class Meta:
        model = Operation
        fields = [
            "id",
            "wallet",
        ]

    def _validate_wallet(self, attrs, free=None, frozen=None):
        free = free or attrs.get("amount_free")
        frozen = frozen or attrs.get("amount_frozen")
        if free and attrs["wallet"].free < free:
            raise ValidationError(_("Insufficient free funds."))
        if frozen and attrs["wallet"].frozen < frozen:
            raise ValidationError(_("Insufficient frozen funds."))

    def create(self, validated_data):
        OperationConfirmation.objects.all().delete()
        validated_data["type"] = self.operation_type
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            "id": instance.id,
            "confirmations": [
                confirmation.destination
                for confirmation in instance.confirmations.all()
            ],
            **data,
        }


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
                _("Minimum program deposit") + f" = {attrs['program'].min_deposit}"
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
            raise ValidationError(_("Minimum program replenishment") + " = 100")
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
                _("Minimum replenishment amount after cancellation") + " - 100 USDT"
            )
        if remainder < 0:
            raise ValidationError(_("Insufficient funds to cancel"))
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
                _("Minimum program deposit after cancellation")
                + f" - {min_deposit} USDT"
            )
        if remainder < 0:
            raise ValidationError(_("Insufficient program deposit"))
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
        if attrs["wallet"] == attrs["receiver"]:
            raise ValidationError(_("Recipient and sender must be different"))
        return attrs

    def create(self, validated_data: dict):
        return super().create(validated_data)


class WalletReplenishmentSerializer(OperationCreateSerializer):
    operation_type = Operation.Type.REPLENISHMENT

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + ["amount", "address"]
        extra_kwargs = {f: {"required": True} for f in fields}
        extra_kwargs["address"].update({"required": False})

    @staticmethod
    def cancel(instance: Operation):
        instance.delete()
        raise ServiceUnavailable(
            detail=_("Сервис эквайринга временно не доступен, повторите попытку позже")
        )

    def create(self, validated_data):
        operation: Operation = super().create(validated_data)
        hook = f"{settings.NODE_JS_URL}/api/operations/"
        data = {"uuid": str(operation.uuid), "expectedAmount": str(operation.amount)}
        headers = {
            "Content-Type": "application/json",
            "x-auth-token": settings.NODE_JS_TOKEN,
        }
        try:
            result = requests.post(hook, json.dumps(data), headers=headers)
        except requests.exceptions.ConnectionError:
            self.cancel(operation)

        if result.status_code != 201:
            self.cancel(operation)

        operation.address = json.loads(result.text).get("walletAddress")
        operation.save()
        return operation

    def to_representation(self, instance: Operation):
        data = super().to_representation(instance)
        return data | {"address": instance.address}


class WalletWithdrawalSerializer(OperationCreateSerializer):
    operation_type = Operation.Type.WITHDRAWAL

    class Meta(OperationCreateSerializer.Meta):
        fields = OperationCreateSerializer.Meta.fields + ["amount", "address"]
        extra_kwargs = {f: {"required": True} for f in fields}

    def validate(self, attrs):
        self._validate_wallet(attrs, free=attrs["amount"])
        return attrs


class OperationReplenishmentConfirmSerializer(Serializer):
    amount = DecimalField(**decimal_usdt)
    status = CharField(required=False)


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
