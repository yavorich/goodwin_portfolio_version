from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from apps.finance.models import Program, UserProgram, UserProgramReplenishment


class OperationViewMixin:
    def get_object(self):
        try:
            return super().get_object()
        except AssertionError:
            return None

    def get_extended_data(self):
        data = self.request.data.copy()
        if not isinstance(data, dict):
            data = data.dict()
        data.update(
            {
                "wallet": self.request.user.wallet,
            }
        )
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
