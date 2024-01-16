from rest_framework.serializers import ModelSerializer, EmailField, CharField
from rest_framework.validators import UniqueValidator
from rest_framework.exceptions import ValidationError
from accounts.models import User


class RegisterUserSerializer(ModelSerializer):
    email = EmailField(validators=[UniqueValidator(queryset=User.objects.all())])
    password2 = CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "password2",
            "region",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def create(self, validated_data):
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        user = User.objects.create_user(email, password, **validated_data)
        return user

    def validate(self, data):
        password = data.get("password")
        password2 = data.pop("password2")
        if password != password2:
            raise ValidationError("Passwords do not match")
        return data


class LoginUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "password",
        ]


class PasswordRecoverUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
        ]


class EmailConfirmUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "confirmation_code",
        ]
