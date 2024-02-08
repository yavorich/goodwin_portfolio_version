from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User


class RecoverPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    password2 = serializers.CharField()

    def validate(self, data):
        password = data.get("password")
        password2 = data.get("password2")
        if password != password2:
            raise ValidationError("Passwords do not match")
        return data


class TokenSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        user = User.objects.filter(email=attrs["email"]).first()
        if user is None:
            raise ValidationError({"email": "Пользователя с таким email не существует"})
        attrs["user"] = user
        return attrs
