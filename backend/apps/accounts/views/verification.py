from django.http import Http404
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from apps.accounts.serializers import (
    PersonalVerificationSerializer,
    AddressVerificationSerializer,
    VerificationStatusSerializer,
)
from apps.accounts.models import User


class VerificationAPIView(RetrieveUpdateAPIView, CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = {
        "personal": PersonalVerificationSerializer,
        "address": AddressVerificationSerializer,
    }

    def get_object(self):
        return get_object_or_404(User, pk=self.request.user.pk)

    def get_serializer_class(self):
        verification_type = self.request.query_params.get("type")
        available_types = list(self.serializer_class.keys())
        if self.request.method == "POST" and verification_type not in available_types:
            raise ValueError(
                f"Query parameter 'type' must be one of: {available_types}"
            )
        return self.serializer_class[verification_type]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def retrieve(self, request, *args, **kwargs):
        instance: User = self.get_object()
        verification_type = self.request.query_params.get("type")

        match verification_type:
            case "personal":
                try:
                    serializer = self.get_serializer(
                        instance.personal_verification,
                    )
                except User.personal_verification.RelatedObjectDoesNotExist:
                    raise Http404
            case "address":
                try:
                    serializer = self.get_serializer(instance.address_verification)
                except User.address_verification.RelatedObjectDoesNotExist:
                    raise Http404
            case _:
                serializer = VerificationStatusSerializer(
                    instance, context={"user": request.user}
                )

        return Response(serializer.data)
