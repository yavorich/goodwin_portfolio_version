from django.http import Http404
from rest_framework.generics import (
    CreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from apps.accounts.serializers import (
    PersonalVerificationSerializer,
    AddressVerificationSerializer,
    VerificationStatusSerializer,
)
from apps.accounts.models import User, PersonalVerification


class VerificationAPIView(RetrieveUpdateAPIView, CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = {
        "personal": PersonalVerificationSerializer,
        "address": AddressVerificationSerializer,
    }

    def validate_verification_type(self):
        verification_type = self.kwargs.get("verification_type")
        if verification_type not in set(self.serializer_class.keys()):
            raise Http404
        return verification_type

    def get_object(self):
        verification_type = self.kwargs.get("verification_type")
        user = self.request.user
        verification_object = None

        match verification_type:
            case "personal":
                verification_object = getattr(user, "personal_verification", None)
            case "address":
                verification_object = getattr(user, "address_verification", None)

        if verification_object is None:
            raise Http404

        return verification_object

    def get_serializer_class(self):
        verification_type = self.kwargs.get("verification_type")
        return self.serializer_class[verification_type]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def retrieve(self, request, *args, **kwargs):
        self.validate_verification_type()
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self.validate_verification_type()
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        self.validate_verification_type()
        return super().create(request, *args, **kwargs)


class VerificationStatusAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerificationStatusSerializer

    def get_object(self):
        return self.request.user
