from rest_framework.fields import UUIDField
from rest_framework.serializers import ModelSerializer, CharField, Serializer
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User, Settings, SettingsAuthCodes
from apps.accounts.serializers.partner import (
    PartnerRetrieveSerializer,
    PartnerSerializer,
)


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
    region = PartnerRetrieveSerializer()
    partner_profile = PartnerSerializer()
    settings = ProfileSettingsSerializer()

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "region",
            "avatar",
            "telegram",
            "settings",
            "partner_profile",
        ]
        read_only_fields = fields


class ProfileUpdateSerializer(ModelSerializer):
    full_name = CharField()

    class Meta:
        model = User
        required_fields = [
            "full_name",
            "email",
            "telegram",
        ]
        fields = required_fields + ["avatar"]

    def validate(self, attrs):
        for f in self.Meta.required_fields:
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
        if "avatar" in validated_data:
            instance.avatar = validated_data["avatar"]

        # for attr in validated_data["settings"].keys():
        #     setattr(instance.settings, attr, validated_data["settings"][attr])
        #
        # instance.settings.save()
        instance.save()

        return instance


class PasswordChangeSerializer(Serializer):
    old_password = CharField()
    new_password = CharField()
    new_password2 = CharField()

    def validate(self, attrs):
        user: User = self.context["user"]
        if not user.check_password(attrs["old_password"]):
            raise ValidationError("Old password is incorrect")
        if attrs["new_password"] != attrs["new_password2"]:
            raise ValidationError("Password mismatch")
        return attrs


class SettingsAuthCodeSerializer(ModelSerializer):
    token = UUIDField(format="hex_verbose")

    class Meta:
        model = SettingsAuthCodes
        fields = ["id", "user", "token", "auth_code", "created_at", "request_body"]
