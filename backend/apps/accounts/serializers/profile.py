from rest_framework.fields import UUIDField
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    Serializer,
    SerializerMethodField,
)
from rest_framework.exceptions import ValidationError

from apps.accounts.models import (
    User,
    Settings,
    SettingsAuthCodes,
    PasswordChangeConfirmation,
    EmailChangeConfirmation,
    ErrorType,
)
from core.serializers import HttpsFileField
from core.utils.error import get_error
from .partner import PartnerSerializer


class ProfileSettingsSerializer(ModelSerializer):
    class Meta:
        model = Settings
        fields = [
            "email_request_code_on_auth",
            "email_request_code_on_withdrawal",
            "email_request_code_on_transfer",
            "telegram_request_code_on_auth",
            "telegram_request_code_on_withdrawal",
            "telegram_request_code_on_transfer",
        ]


class InviterSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "full_name",
            "email",
        ]


class ProfileRetrieveSerializer(ModelSerializer):
    avatar = HttpsFileField()
    settings = ProfileSettingsSerializer()
    partner = SerializerMethodField()
    is_partner = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "avatar",
            "telegram",
            "settings",
            "partner",
            "is_partner",
        ]
        read_only_fields = fields

    def get_partner(self, obj):
        partner = obj.partner or getattr(obj, "partner_profile", None)
        if partner:
            return PartnerSerializer(instance=partner).data
        return None

    def get_is_partner(self, obj):
        return getattr(obj, "partner_profile", None) is not None


class ProfileUpdateSerializer(ModelSerializer):
    full_name = CharField()
    avatar = HttpsFileField()

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
            get_error(error_type=ErrorType.SAME_EMAIL)

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
            # instance.email = validated_data["email"]
            pass

        if "telegram" in validated_data:
            instance.telegram = validated_data["telegram"]

        if "avatar" in validated_data:
            instance.avatar = validated_data["avatar"]

        instance.save()

        return instance


class PasswordChangeSerializer(Serializer):
    old_password = CharField()
    new_password = CharField()
    new_password2 = CharField()

    def validate(self, attrs):
        user: User = self.context["user"]
        if not user.check_password(attrs["old_password"]):
            get_error(error_type=ErrorType.INVALID_PASSWORD)
        if attrs["new_password"] != attrs["new_password2"]:
            get_error(error_type=ErrorType.PASSWORD_MISMATCH)
        return attrs


class SettingsAuthCodeSerializer(ModelSerializer):
    token = UUIDField(format="hex_verbose")

    class Meta:
        model = SettingsAuthCodes
        fields = ["id", "user", "token", "auth_code", "created_at", "request_body"]


class PasswordAuthCodeSerializer(ModelSerializer):
    token = UUIDField(format="hex_verbose")

    class Meta:
        model = PasswordChangeConfirmation
        fields = ["id", "user", "token", "auth_code", "created_at"]


class EmailAuthCodeSerializer(ModelSerializer):
    token = UUIDField(format="hex_verbose")

    class Meta:
        model = EmailChangeConfirmation
        fields = ["id", "user", "token", "auth_code", "created_at", "email"]
