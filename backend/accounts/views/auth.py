from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.decorators import action
from accounts.serializers import (
    LoginUserSerializer,
    RegisterUserSerializer,
    PasswordRecoverUserSerializer,
    EmailConfirmUserSerializer,
)
from accounts.models import User


class AuthViewSet(CreateAPIView, GenericViewSet):
    serializer_class = {
        "register": RegisterUserSerializer,
        "login": LoginUserSerializer,
        "recover_password": PasswordRecoverUserSerializer,
        "confirm": EmailConfirmUserSerializer,
    }
    queryset = User.objects.all()

    def get_serializer_class(self):
        return self.serializer_class[self.action]

    @action(methods=["post"], detail=False)
    def register(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return response

    @action(methods=["post"], detail=True)
    def login(self, request, pk=None):
        pass

    @action(methods=["post"], detail=True)
    def confirm(self, request, pk=None):
        pass

    @action(methods=["post"], detail=True)
    def recover_password(self, request, pk=None):
        pass
