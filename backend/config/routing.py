from django.urls import path
from channels.routing import URLRouter

from apps.accounts.urls import websocket_urlpatterns as accounts_websocket_urlpatterns


websocket_urlpatterns = [
    path("ws/", URLRouter(accounts_websocket_urlpatterns)),
]
