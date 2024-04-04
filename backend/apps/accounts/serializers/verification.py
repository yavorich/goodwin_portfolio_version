from rest_framework.serializers import ModelSerializer, FileField, CharField
from apps.accounts.models import (
    PersonalVerification,
    AddressVerification,
    VerificationStatus,
    User,
)

from core.utils import validate_file_size


class PersonalVerificationSerializer(ModelSerializer):
    file = FileField(
        validators=[validate_file_size],
        required=True,
        allow_null=False,
        allow_empty_file=False,
    )

    class Meta:
        model = PersonalVerification
        fields = [
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "document_type",
            "document_issue_date",
            "document_issue_region",
            "file",
            "status",
            "reject_message",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}
        read_only_fields = ["status", "reject_message"]

    def create(self, validated_data):
        validated_data["status"] = VerificationStatus.CHECK
        validated_data["reject_message"] = ""
        instance, created = PersonalVerification.objects.update_or_create(
            user=self.context.get("user"), defaults=validated_data
        )
        return instance

    def update(self, instance, validated_data):
        validated_data["status"] = VerificationStatus.CHECK
        validated_data["reject_message"] = ""
        instance, created = PersonalVerification.objects.update_or_create(
            user=self.context.get("user"), defaults=validated_data
        )
        return instance


class AddressVerificationSerializer(ModelSerializer):
    file = FileField(validators=[validate_file_size])

    class Meta:
        model = AddressVerification
        fields = [
            "country",
            "city",
            "address",
            "postal_code",
            "file",
            "status",
            "reject_message",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}
        read_only_fields = ["status", "reject_message"]

    def create(self, validated_data):
        validated_data["status"] = VerificationStatus.CHECK
        instance, created = AddressVerification.objects.update_or_create(
            user=self.context.get("user"), defaults=validated_data
        )
        return instance

    def update(self, instance, validated_data):
        validated_data["status"] = VerificationStatus.CHECK
        instance, created = AddressVerification.objects.update_or_create(
            user=self.context.get("user"), defaults=validated_data
        )
        return instance


class VerificationStatusSerializer(ModelSerializer):
    status_personal = CharField(source="personal_verification.status")
    status_address = CharField(source="address_verification.status")
    personal_reject_message = CharField(source="personal_verification.reject_message")
    address_reject_message = CharField(source="address_verification.reject_message")

    class Meta:
        model = User
        fields = [
            "status_personal",
            "personal_reject_message",
            "status_address",
            "address_reject_message",
        ]
