from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import PreAuthToken
from apps.accounts.serializers import (
    TokenObtainPairEmailConfirmSerializer,
    LoginConfirmSerializer,
)
from config.settings import PRE_AUTH_CODE_EXPIRES


class LoginAPIView(TokenObtainPairView):
    serializer_class = TokenObtainPairEmailConfirmSerializer


class LoginConfirmView(GenericAPIView):
    serializer_class = LoginConfirmSerializer

    def post(self, request, *args, **kwargs):
        service_type = self.kwargs["service_type"]
        if service_type not in ("telegram", "email"):
            raise NotFound

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]
        token = serializer.validated_data["token"]

        user, is_authenticated = PreAuthToken.objects.verify_code(
            verify_type=PreAuthToken.VerifyType.AUTHORIZATION,
            service_type=service_type,
            token=token,
            code=code,
        )
        response_data = {"is_authenticated": is_authenticated}

        if is_authenticated:
            refresh = RefreshToken.for_user(user)
            response_data.update(
                {
                    "id": user.pk,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            )

        return Response(response_data)
