from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from apps.information.models import Program, UserProgram
from apps.information.serializers import (
    ProgramListSerializer,
    UserProgramListSerializer,
)


class ProgramAPIView(ListAPIView):
    serializer_class = ProgramListSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        status = self.request.query_params.get("status")
        if not status:
            return ProgramListSerializer
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
        programs = UserProgram.objects.filter(user=self.request.user)
        return filter(lambda x: x.status == status, programs)
