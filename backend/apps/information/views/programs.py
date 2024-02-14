from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from apps.information.models import (
    Program,
    UserProgram,
    UserProgramReplenishment,
)
from apps.information.serializers import (
    ProgramSerializer,
    UserProgramSerializer,
    UserProgramReplenishmentSerializer,
    program_operations_serializers,
)
from core.views import OperationViewMixin


class ProgramMixin(OperationViewMixin, ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            if self.action == "all":
                return ProgramSerializer
            if self.action == "replenishments":
                return UserProgramReplenishmentSerializer
            return UserProgramSerializer
        return program_operations_serializers[self.action]

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
