from rest_framework.serializers import ModelSerializer, CharField
from rest_framework.exceptions import ValidationError

from accounts.models import User, Settings


class ProfileSettingsSerializer(ModelSerializer):
    class Meta:
        model = Settings
        fields = [
            "email_request_code_on_auth",
            "email_request_code_on_withdrawal",
            "telegram_request_code_on_auth",
            "telegram_request_code_on_withdrawal",
        ]


class InviterSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "full_name",
            "email",
        ]


class ProfileRetrieveSerializer(ModelSerializer):
    inviter = InviterSerializer()
    settings = ProfileSettingsSerializer()

    class Meta:
        model = User
        fields = [
            "full_name",
            "id",
            "email",
            "telegram",
            "inviter",
            "settings",
        ]


class ProfileUpdateSerializer(ModelSerializer):
    full_name = CharField()
    settings = ProfileSettingsSerializer()

    class Meta:
        model = User
        fields = [
            "full_name",
            "email",
            "telegram",
            "settings",
        ]

    def validate(self, attrs):
        for f in self.Meta.fields:
            if f not in attrs:
                raise ValidationError(f"{f} is required")
        if (
            User.objects.filter(email=attrs["email"])
            .exclude(pk=self.context["user"].pk)
            .exists()
        ):
            raise ValidationError("Email is already taken")

        if len(attrs["full_name"].split()) != 2:
            raise ValidationError(
                "'Name and surname' value must include exactly 2 words"
            )
        return attrs

    def update(self, instance: User, validated_data):
        instance.first_name, instance.last_name = validated_data["full_name"].split()

        if instance.email != validated_data["email"]:
            instance.email_is_confirmed = False

        instance.email = validated_data["email"]
        instance.telegram = validated_data["telegram"]

        for attr in validated_data["settings"].keys():
            setattr(instance.settings, attr, validated_data["settings"][attr])

        instance.settings.save()
        instance.save()

        return instance
