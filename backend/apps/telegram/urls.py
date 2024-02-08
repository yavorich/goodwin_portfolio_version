from django.urls import path

from apps.telegram.views import (
    ConnectTelegramView,
    DisconnectTelegramView,
    disable_telegram_notify,
)

urlpatterns = [
    path("connect/", ConnectTelegramView.as_view(), name="connect_telegram"),
    path("disconnect/", DisconnectTelegramView.as_view(), name="disconnect_telegram"),
    path("disconnect/link/", disable_telegram_notify, name="disconnect_telegram_link"),
]
