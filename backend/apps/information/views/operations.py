from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_200_OK
from rest_framework.response import Response
from django.utils.timezone import now

from apps.information.models import Operation, Action
from apps.information.serializers import OperationSerializer
from apps.accounts.serializers import UserEmailConfirmSerializer
from config.settings import DEBUG


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
