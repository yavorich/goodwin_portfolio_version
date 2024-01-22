from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from accounts.serializers import (
    PersonalVerificationSerializer,
    AddressVerificationSerializer,
    VerificationStatusSerializer,
)
from accounts.models import User


class VerificationAPIView(RetrieveAPIView, CreateAPIView):
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
        instance = self.get_object()
        serializer = VerificationStatusSerializer(
            instance, context={"user": request.user}
        )
        return Response(serializer.data)
