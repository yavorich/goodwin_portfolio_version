from rest_framework.serializers import (
    ModelSerializer,
    CharField,
)
from rest_framework.exceptions import ValidationError

from apps.information.models import Operation, Wallet, Action


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

    class Meta:
        model = Operation
        fields = [
            "id",
            "type",
            "wallet",
            "program",
            "user_program",
            "replenishment",
            "frozen_item",
            "amount",
            "amount_free",
            "amount_frozen",
            "confirmed",
        ]

    def _validate_wallet(self, wallet: Wallet, free=0.0, frozen=0.0):
        if wallet.free < free:
            raise ValidationError("Insufficient free funds.")
        if wallet.frozen < frozen:
            raise ValidationError("Insufficient frozen funds.")

    def validate(self, attrs):
        wallet: Wallet = attrs["wallet"]
        program = attrs.get("program")
        user_program = attrs.get("user_program")
        replenishment = attrs.get("replenishment")
        amount = attrs.get("amount")
        free = attrs.get("amount_free")
        frozen = attrs.get("amount_frozen")
        # option = self.context.get("option")
        _type: Operation.Type = attrs["type"]

        types = Operation.Type

        if _type == types.PROGRAM_START:
            self._validate_wallet(wallet, free=free, frozen=frozen)
            if free + frozen < program.min_deposit:
                raise ValidationError(
                    f"Minimum program deposit = {program.min_deposit}"
                )

        if _type == types.PROGRAM_REPLENISHMENT:
            self._validate_wallet(wallet, free=free, frozen=frozen)
            if free + frozen < 100:
                raise ValidationError(f"Minimum program replenishment = {100}")

        if _type == types.PROGRAM_REPLENISHMENT_CANCEL:
            if 0 < replenishment.amount - amount < 100:
                raise ValidationError(
                    "Minimum replenishment amount after cancellation - 100 USDT"
                )

        if _type == types.PROGRAM_CLOSURE:
            min_deposit = user_program.program.min_deposit
            if 0 < user_program.funds - amount < min_deposit:
                raise ValidationError(
                    f"Minimum program deposit after cancellation - {min_deposit} USDT"
                )

        if _type == types.DEFROST:
            self._validate_wallet(wallet, frozen=amount)

        return attrs
