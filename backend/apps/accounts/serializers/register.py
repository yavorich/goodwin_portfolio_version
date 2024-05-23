from rest_framework.serializers import (
    ModelSerializer,
    EmailField,
    CharField,
)

from apps.accounts.models import User, RegisterConfirmation, ErrorType
from core.utils.error import get_error


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
            "partner",
        ]
        # extra_kwargs = {f: {"required": True} for f in fields}

    @staticmethod
    def validate_email(value):
        if User.objects.filter(email=value).exists():
            get_error(error_type=ErrorType.SAME_EMAIL)
        return value

    def validate(self, data):
        password = data.get("password")
        password2 = data.pop("password2")
        if password != password2:
            get_error(error_type=ErrorType.PASSWORD_MISMATCH)
        return data

    def create(self, validated_data):
        return RegisterConfirmation.objects.send_code(validated_data)
