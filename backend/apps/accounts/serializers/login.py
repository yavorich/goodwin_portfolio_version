from typing import Dict, Any

from django.contrib.auth.models import update_last_login
from rest_framework.serializers import Serializer, UUIDField, CharField
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from apps.accounts.models import PreAuthToken


class TokenObtainPairEmailConfirmSerializer(TokenObtainPairSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        data = super(TokenObtainPairSerializer, self).validate(attrs)

        is_authenticated, confirmation_data = PreAuthToken.objects.send_code(
            PreAuthToken.VerifyType.AUTHORIZATION, self.user
        )

        data["is_authenticated"] = is_authenticated
        if is_authenticated:
            data["id"] = self.user.id
            refresh = self.get_token(self.user)
            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)
            update_last_login(None, self.user)

        else:
            data.update(confirmation_data)

        return data


class LoginConfirmSerializer(Serializer):
    token = UUIDField()
    code = CharField(min_length=10, max_length=10)


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        refresh = self.token_class(attrs["refresh"])
        return {"access": str(refresh.access_token), "refresh": str(refresh)}
