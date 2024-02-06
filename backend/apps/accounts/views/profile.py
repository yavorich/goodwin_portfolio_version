from django.http import Http404
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.accounts.models import User, SettingsAuthCodes
from apps.accounts.permissions import IsAuthenticatedAndVerified
from apps.accounts.serializers import (
    ProfileRetrieveSerializer,
    ProfileUpdateSerializer,
    PasswordChangeSerializer,
)
from apps.accounts.serializers.profile import ProfileSettingsSerializer


class ProfileAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = {
        "GET": ProfileRetrieveSerializer,
        "PATCH": ProfileUpdateSerializer,
    }
    queryset = User.objects.all()

    def get_serializer_class(self):
        return self.serializer_class[self.request.method]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def get_object(self):
        return get_object_or_404(User, pk=self.request.user.pk)


class PasswordChangeAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.data["new_password"])
        request.user.save()
        return Response({"success": "Пароль успешно обновлен"})


class SettingsAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = ProfileSettingsSerializer

    def get_object(self):
        user = self.request.user
        settings = getattr(user, "settings", None)
        if settings is None:
            raise Http404
        return settings

    def update(self, request, *args, **kwargs):
        current_settings_serializer = self.get_serializer(self.get_object())

        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_auth_code = None
        if current_settings_serializer.data != serializer.data:
            new_auth_code = SettingsAuthCodes.objects.create(
                user=request.user,
                auth_code=SettingsAuthCodes.generate_code(),
                request_body=serializer.data,
            )

        return Response(
            {
                "token": new_auth_code.token if new_auth_code else None,
                "updated_data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
