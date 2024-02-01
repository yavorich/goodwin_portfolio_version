from django.shortcuts import redirect
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from apps.telegram.models import ConfirmationCode
from apps.telegram.utils import send_telegram_message
from config.settings import TELEGRAM_BOT_NAME


class ConnectTelegramView(GenericAPIView):
    """Ссылка для подключения уведомлений в телеграм"""

    permission_classes = [IsAuthenticated]
    serializer_class = Serializer

    def get(self, request, *args, **kwargs):
        code = ConfirmationCode.objects.generate(user=request.user)
        return Response({"url": f"https://t.me/{TELEGRAM_BOT_NAME}?start={code.code}"})


class DisconnectTelegramView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = Serializer

    def post(self, request, *args, **kwargs):
        disable_telegram_notify(request)
        return Response({"status": "success"})


def disable_telegram_notify(request):
    user = request.user
    if user.is_authenticated and user.telegram_id is not None:
        telegram_id = user.telegram_id
        user.telegram_id = None
        user.telegram = None
        user.save()
        send_telegram_message(telegram_id, "Уведомления для телеграмма отвязаны!")

    return redirect(f"https://t.me/{TELEGRAM_BOT_NAME}")
