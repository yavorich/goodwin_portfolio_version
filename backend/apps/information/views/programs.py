from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from apps.information.models import (
    Program,
    UserProgram,
    Operation,
    UserProgramReplenishment,
)
from apps.information.serializers import (
    ProgramSerializer,
    UserProgramSerializer,
    OperationCreateSerializer,
    UserProgramReplenishmentSerializer,
)


class ProgramMixin(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            if self.action == "all":
                return ProgramSerializer
            if self.action == "replenishments":
                return UserProgramReplenishmentSerializer
            return UserProgramSerializer
        return OperationCreateSerializer

    def get_object(self):
        try:
            return super().get_object()
        except AssertionError:
            return None

    def get_queryset(self):
        if self.action in ["start", "all"]:
            return Program.objects.all()

        user_programs = UserProgram.objects.filter(wallet=self.request.user.wallet)

        if self.action == "waiting":
            return user_programs.filter(status=UserProgram.Status.INITIAL)

        if self.action == "running":
            return user_programs.filter(status=UserProgram.Status.RUNNING)

        if self.action == "replenishments":
            return UserProgramReplenishment.objects.filter(
                program__in=user_programs,
                status=UserProgramReplenishment.Status.INITIAL,
            )
        if self.action == "cancel":
            return UserProgramReplenishment.objects.filter(
                program__pk=self.kwargs["program_pk"],
                status=UserProgramReplenishment.Status.INITIAL,
            )

        return user_programs

    def get_extended_data(self):
        data = self.request.data
        if data:
            data = data.dict()
        operation_types = {
            "start": Operation.Type.PROGRAM_START,
            "replenish": Operation.Type.PROGRAM_REPLENISHMENT,
            "cancel": Operation.Type.PROGRAM_REPLENISHMENT_CANCEL,
            "close": Operation.Type.PROGRAM_EARLY_CLOSURE,
        }
        operation_type = operation_types[self.action]
        data |= {
            "type": operation_type,
            "wallet": self.request.user.wallet.pk,
        }
        instance = self.get_object()
        if isinstance(instance, Program):
            data["program"] = instance.pk
        elif isinstance(instance, UserProgram):
            data["user_program"] = instance.pk
        elif isinstance(instance, UserProgramReplenishment):
            data["replenishment"] = instance.pk
        return data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.get_extended_data())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)


class ProgramViewSet(ProgramMixin):

    @action(methods=["get"], detail=False)
    def all(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(methods=["get"], detail=False)
    def waiting(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(methods=["get"], detail=False)
    def running(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(methods=["post"], detail=True)
    def start(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    @action(methods=["post"], detail=True)
    def close(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    @action(methods=["post"], detail=True)
    def replenish(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    @action(methods=["get"], detail=False)
    def replenishments(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ProgramReplenishmentViewSet(ProgramMixin):

    @action(methods=["post"], detail=True)
    def cancel(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
