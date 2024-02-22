from rest_framework.fields import UUIDField
from rest_framework.serializers import ModelSerializer, CharField, Serializer
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User, Settings, SettingsAuthCodes
from apps.accounts.models.user import Partner
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
    # region = PartnerRetrieveSerializer()
    partner_profile = PartnerSerializer()
    settings = ProfileSettingsSerializer()

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "partner_label",
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
        fields = [
            "full_name",
            "email",
            "avatar",
            "telegram",
        ]

    def validate(self, attrs):
        if "email" in attrs and (
            User.objects.filter(email=attrs["email"])
            .exclude(pk=self.context["user"].pk)
            .exists()
        ):
            raise ValidationError("Email is already taken")

        if "full_name" in attrs and len(attrs["full_name"].split()) != 2:
            raise ValidationError(
                "'Name and surname' value must include exactly 2 words"
            )
        return attrs

    def update(self, instance: User, validated_data):
        if "full_name" in validated_data:
            values = validated_data["full_name"].split()
            instance.first_name, instance.last_name = values

        if "email" in validated_data:
            instance.email = validated_data["email"]

        if "telegram" in validated_data:
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
