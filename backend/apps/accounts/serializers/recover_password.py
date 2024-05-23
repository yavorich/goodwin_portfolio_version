from rest_framework import serializers

from apps.accounts.models import User, ErrorType
from core.utils.error import get_error


class RecoverPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    password2 = serializers.CharField()

    def validate(self, data):
        password = data.get("password")
        password2 = data.get("password2")
        if password != password2:
            get_error(error_type=ErrorType.PASSWORD_MISMATCH)
        return data


class TokenSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        user = User.objects.filter(email=attrs["email"]).first()
        if user is None:
            get_error(error_type=ErrorType.INVALID_EMAIL)
        attrs["user"] = user
        return attrs
