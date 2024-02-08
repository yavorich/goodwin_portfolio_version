from rest_framework import status
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.generics import RetrieveUpdateAPIView, GenericAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User, SettingsAuthCodes
from apps.accounts.models.settings_auth_codes import DestinationType
from apps.accounts.permissions import IsAuthenticatedAndVerified
from apps.accounts.serializers import (
    ProfileRetrieveSerializer,
    ProfileUpdateSerializer,
    PasswordChangeSerializer,
)
from apps.accounts.serializers.profile import (
    ProfileSettingsSerializer,
    SettingsAuthCodeSerializer,
)
from apps.accounts.services import send_email_change_settings
from apps.telegram.utils import (
    send_telegram_message,
)


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
        return self.request.user.settings

    def update(self, request, *args, **kwargs):
        current_settings_serializer = self.get_serializer(self.get_object())

        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        tokens = {}
        changed_fields = []

        for key, value in serializer.validated_data.items():
            if current_settings_serializer.data.get(key) != value:
                changed_fields.append(key)

        if len(changed_fields) > 0:
            destinations = set()

            for field in changed_fields:
                destinations.add(field.split("_")[0])

            for destination in destinations:
                new_auth_code = SettingsAuthCodes.objects.create(
                    user=request.user,
                    auth_code=SettingsAuthCodes.generate_code(),
                    request_body={
                        key: value
                        for key, value in serializer.data.items()
                        if key.startswith(destination)
                    },
                    destination=destination,
                )

                if new_auth_code.destination == DestinationType.EMAIL:
                    send_email_change_settings(
                        user=request.user, code=new_auth_code.auth_code
                    )
                    tokens[DestinationType.EMAIL] = new_auth_code.token
                elif new_auth_code.destination == DestinationType.TELEGRAM:
                    send_telegram_message(
                        telegram_id=request.user.telegram_id,
                        text=_(
                            "Смена настроек\nВаш код для подтверждения смены настроек"
                        )
                        + f": {new_auth_code.auth_code}",
                    )
                    tokens[DestinationType.TELEGRAM] = new_auth_code.token

        return Response(
            {
                "token": tokens,
                "updated_data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class SettingsConfirmCreateView(CreateAPIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = SettingsAuthCodeSerializer

    def get_object(self):
        destination = self.kwargs.get("destination")
        if destination not in DestinationType:
            raise NotFound()

        serializer = self.get_serializer(data=self.request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        settings_auth_code_object = SettingsAuthCodes.objects.filter(
            user=self.request.user,
            auth_code=serializer.validated_data.get("auth_code"),
            token=serializer.validated_data.get("token"),
            destination=destination,
        ).first()

        if settings_auth_code_object is None:
            raise ParseError(detail=_("Код подтверждения не найден"))

        return settings_auth_code_object

    def create(self, request, *args, **kwargs):
        settings_auth_code_object = self.get_object()
        user = settings_auth_code_object.user
        unsaved_settings = settings_auth_code_object.request_body

        settings = user.settings

        for key, value in unsaved_settings.items():
            setattr(settings, key, value)
        settings.save()

        settings_serializer = ProfileSettingsSerializer(settings)

        settings_auth_code_object.delete()
        return Response(settings_serializer.data, status=status.HTTP_200_OK)
