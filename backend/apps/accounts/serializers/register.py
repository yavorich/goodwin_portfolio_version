from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    ModelSerializer,
    EmailField,
    CharField,
)

from apps.accounts.models import User, RegisterConfirmation


class RegisterUserSerializer(ModelSerializer):
    email = EmailField()
    password2 = CharField(write_only=True)

    class Meta:
        model = RegisterConfirmation
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "password2",
            "region",
        ]
        # extra_kwargs = {f: {"required": True} for f in fields}

    @staticmethod
    def validate_email(value):
        if User.objects.filter(email=value).exists():
            raise ValidationError(_("Пользователь с данной почтой уже существует"))
        return value

    def validate(self, data):
        password = data.get("password")
        password2 = data.pop("password2")
        if password != password2:
            raise ValidationError("Пароли не совпадают")
        return data

    def create(self, validated_data):
        return RegisterConfirmation.objects.send_code(validated_data)
