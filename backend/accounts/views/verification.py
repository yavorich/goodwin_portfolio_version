from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.serializers import (
    PersonalVerificationSerializer,
    AddressVerificationSerializer,
)


class VerificationAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = {
        "personal": PersonalVerificationSerializer,
        "address": AddressVerificationSerializer,
    }

    def get_serializer_class(self):
        verification_type = self.request.query_params.get("type")
        available_types = list(self.serializer_class.keys())
        if verification_type not in available_types:
            raise ValueError(
                f"Query parameter 'type' must be one of: {available_types}"
            )
        return self.serializer_class[verification_type]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context
