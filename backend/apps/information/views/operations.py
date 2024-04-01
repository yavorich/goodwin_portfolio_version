from decimal import Decimal

import requests
from django.utils.timezone import now
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    ListAPIView,
    UpdateAPIView,
    get_object_or_404,
    GenericAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from apps.accounts.permissions import IsLocal, IsAuthenticatedAndVerified
from apps.accounts.serializers import UserEmailConfirmSerializer
from apps.information.models import Operation, Action
from apps.information.serializers import OperationSerializer
from apps.information.serializers.operations import (
    OperationReplenishmentConfirmSerializer,
)
from apps.information.services.operation_replenishment_confirmation import (
    operation_replenishment_confirmation,
)
from config import settings
from config.settings import DEBUG
from core.exceptions import ServiceUnavailable


class OperationAPIView(ListAPIView):
    serializer_class = OperationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Action.objects.filter(
            operation__wallet=self.request.user.wallet,  # confirmed=True, done=True
        )

    def filter_queryset(self, queryset):
        _type = self.request.query_params.get("type")
        if _type and _type not in Operation.Type:
            available_types = [e.value for e in Operation.Type]
            raise ValidationError(
                f"Incorrect type='{_type}'. Must be one of {available_types}"
            )
        return queryset.filter(operation__type=_type) if _type else queryset


class OperationConfirmAPIView(UpdateAPIView):
    serializer_class = UserEmailConfirmSerializer
    permission_classes = [IsAuthenticated]
    queryset = Operation.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.data["confirmation_code"]
        operation: Operation = self.get_object()

        if not DEBUG and code != operation.confirmation_code:
            raise ValidationError("Verification code is incorrect.")

        if now() > operation.confirmation_code_expires_at:
            raise ValidationError(
                "Verification code has expired. Repeat the operation."
            )

        operation.confirmed = True
        operation.save()
        operation.apply()

        return Response(status=HTTP_200_OK)


class OperationReplenishmentConfirmView(GenericAPIView):
    permission_classes = [IsLocal]
    serializer_class = OperationReplenishmentConfirmSerializer

    def get_object(self):
        return get_object_or_404(Operation, uuid=self.kwargs["uuid"])

    def post(self, request, *args, **kwargs):
        operation: Operation = self.get_object()

        if operation.done:
            raise ValidationError("Operation already done")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = Decimal(serializer.data["amount"])
        print(operation_replenishment_confirmation(operation, amount))

        return Response(status=status.HTTP_204_NO_CONTENT)


class OperationReplenishmentStatusView(RetrieveAPIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = OperationReplenishmentConfirmSerializer

    def get_object(self):
        user = self.request.user
        operation = get_object_or_404(
            Operation, pk=self.kwargs["pk"], wallet=user.wallet
        )
        return operation

    def get(self, request, *args, **kwargs):
        operation = self.get_object()
        url = f"{settings.NODE_JS_URL}/api/operations/{operation.uuid}/"
        response = requests.patch(url=url)
        if response.status_code != 200:
            raise ServiceUnavailable(
                detail="Сервис эквайринга временно не доступен, повторите попытку позже"
            )
        serializer = self.get_serializer(response)
        serializer.is_valid(raise_exception=True)
        print(serializer.data)
        message = operation_replenishment_confirmation(
            operation, serializer.data.amount
        )
        return {
            "amount_expected": operation.amount,
            "amount_received": serializer.data.amount,
            "message": message,
            "done": operation.done,
        }
