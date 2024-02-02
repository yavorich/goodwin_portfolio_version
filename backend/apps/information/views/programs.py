from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from apps.information.models import Program, UserProgram, Operation
from apps.information.serializers import (
    ProgramSerializer,
    UserProgramListSerializer,
    UserProgramCreateSerializer,
    OperationCreateSerializer,
)


class ProgramAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        status = self.request.query_params.get("status")
        if not status:
            return ProgramSerializer
        return UserProgramListSerializer

    def get_queryset(self):
        status = self.request.query_params.get("status")
        if not status:
            return Program.objects.all()
        if status not in UserProgram.Status:
            available_types = [e.value for e in UserProgram.Status]
            raise ValidationError(
                f"Incorrect status='{status}'. Must be one of {available_types}"
            )
        programs = UserProgram.objects.filter(wallet=self.request.user.wallet)
        return filter(lambda x: x.status == status, programs)


class UserProgramViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OperationCreateSerializer

    def get_queryset(self):
        if self.action == "start":
            return Program.objects.all()
        return UserProgram.objects.all()

    def get_extended_data(self, program: Program | None = None):
        data = self.request.data
        if data:
            data = data.dict()
        operation_types = {
            "start": Operation.Type.PROGRAM_START,
            "replenishment": Operation.Type.PROGRAM_REPLENISHMENT,
            "replenishment_cancel": Operation.Type.PROGRAM_REPLENISHMENT_CANCEL,
            "close": Operation.Type.PROGRAM_EARLY_CLOSURE,
        }
        operation_type = operation_types[self.action]
        program = program or self.get_object()
        data |= {
            "type": operation_type,
            "wallet": self.request.user.wallet.pk,
            "program": program.pk,
        }
        if operation_type == Operation.Type.PROGRAM_EARLY_CLOSURE:
            data["amount_frozen"] = program.funds
            data["amount_free"] = 0.0
        return data

    def create(self, request, *args, **kwargs):
        program = kwargs.get("program")
        serializer = self.get_serializer(data=self.get_extended_data(program))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

    @action(methods=["post"], detail=True)
    def start(self, request, pk=None):
        program_serializer = UserProgramCreateSerializer(
            data=request.data.dict() | {
                "wallet": self.request.user.wallet.pk,
                "program": self.get_object().pk,
            },
        )

        program_serializer.is_valid(raise_exception=True)
        program = program_serializer.save()
        return self.create(request, program=program)

    @action(methods=["post"], detail=True)
    def replenishment(self, request, pk=None):
        return self.create(request)

    @action(methods=["post"], detail=True)
    def replenishment_cancel(self, request, pk=None):
        return self.create(request)

    @action(methods=["post"], detail=True)
    def close(self, request, pk=None):
        return self.create(request)
