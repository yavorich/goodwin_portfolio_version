from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from django.utils import timezone
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.serializers import (
    ResetPasswordSerializer,
    RecoverPasswordSerializer,
    TokenSerializer,
)
from apps.accounts.services import send_email_change_password


class ResetPasswordAPIView(CreateAPIView):
    """Отправить письмо для восстановления аккаунта"""

    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        send_email_change_password(user, request)
        return Response({"success": "Сообщение отправлено"})


class RecoverPasswordAPIView(CreateAPIView):
    """Сменить пароль на введенный"""

    permission_classes = [AllowAny]
    serializer_class = RecoverPasswordSerializer

    def post(self, request, *args, **kwargs):
        # проверка токена на валидность
        token_serializer = TokenSerializer(data=kwargs)
        if not token_serializer.is_valid():
            raise ParseError("Ссылка устарела")

        token = token_serializer.validated_data["token"]
        user = User.objects.filter(
            temp__changing_password_code=token,
            temp__changing_password_code_expires__gte=timezone.now(),
        ).first()
        if user is None:  # если ссылка устарела
            raise ParseError("Ссылка устарела")

        serializer = self.serializer_class(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)

        new_password = serializer.data["password"]
        user.set_password(new_password)
        user.save()

        user.temp.changing_password_code = None
        user.temp.changing_password_code_expires = None
        user.temp.save()
        return Response({"success": "Пароль успешно обновлен"})
