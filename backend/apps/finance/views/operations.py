from decimal import Decimal

import requests
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound, ParseError
from rest_framework.generics import (
    ListAPIView,
    UpdateAPIView,
    get_object_or_404,
    GenericAPIView,
    RetrieveAPIView,
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    DateFromToRangeFilter,
    CharFilter,
    NumberFilter,
)
from django.db.models.functions import Abs
from apps.accounts.permissions import IsLocal, IsAuthenticatedAndVerified

from apps.accounts.serializers import UserEmailConfirmSerializer
from apps.finance.models import (
    Operation,
    OperationHistory,
    OperationConfirmation,
    DestinationType,
)
from apps.finance.models.operation_type import OperationType
from apps.finance.serializers import OperationHistorySerializer
from apps.finance.serializers.operations import (
    OperationReplenishmentConfirmSerializer,
)
from apps.finance.services.operation_replenishment_confirmation import (
    operation_replenishment_confirmation,
)
from config import settings
from core.exceptions import ServiceUnavailable
from core.pagination import PageNumberSetPagination


class OperationHistoryFilterSet(FilterSet):
    operation_type = CharFilter(field_name="operation_type")
    date = DateFromToRangeFilter(field_name="created_at")
    amount_min = NumberFilter(method="filter_amount_min", field_name="amount")
    amount_max = NumberFilter(method="filter_amount_max", field_name="amount")

    def filter_amount_min(self, queryset, field_name, value):
        return queryset.annotate(abs_amount=Abs("amount")).filter(abs_amount__gte=value)

    def filter_amount_max(self, queryset, field_name, value):
        return queryset.annotate(abs_amount=Abs("amount")).filter(abs_amount__lte=value)


class OperationAPIView(ListAPIView):
    serializer_class = OperationHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = OperationHistoryFilterSet

    def get_queryset(self):
        return OperationHistory.objects.filter(wallet=self.request.user.wallet)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        total_data = {
            "total_in": queryset.total_in(),
            "total_out": queryset.total_out(),
        }
        page = self.paginate_queryset(queryset)
        if request.query_params.get("page") and page is not None:
            serializer = self.get_serializer(page, many=True)
            serializer_data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            serializer_data = {"results": serializer.data}
        return Response({**total_data, **serializer_data})


class OperationConfirmAPIView(UpdateAPIView):
    serializer_class = UserEmailConfirmSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        destination = self.kwargs.get("destination")
        if destination not in DestinationType:
            raise NotFound(f'Destination "{destination}" not found')

        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        operation = get_object_or_404(Operation, pk=self.kwargs.get("pk"))

        confirmation_object = OperationConfirmation.objects.filter(
            operation=operation,
            code=serializer.validated_data.get("confirmation_code"),
            destination=destination,
            created_at__gte=now() - settings.OPERATION_CONFIRM_CODE_EXPIRES,
        ).first()

        if confirmation_object is None:
            raise ParseError(detail=_("Код подтверждения не найден"))

        confirmation_object.delete()

        return operation

    def post(self, request, *args, **kwargs):
        operation: Operation = self.get_object()

        if operation.confirmed:
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
        operation: Operation = self.get_object()
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


class OperationTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data = [{"name": str(e), "verbose_name": e.label} for e in OperationType]
        return Response(data=data)
