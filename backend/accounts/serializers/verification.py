from rest_framework.serializers import ModelSerializer, FileField, CharField
from accounts.models import (
    PersonalVerification,
    AddressVerification,
    VerificationStatus,
    User,
)

from core.utils import validate_file_size


class PersonalVerificationSerializer(ModelSerializer):
    file = FileField(validators=[validate_file_size])

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
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def create(self, validated_data):
        validated_data["status"] = VerificationStatus.CHECK
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
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def create(self, validated_data):
        validated_data["status"] = VerificationStatus.CHECK
        instance, created = AddressVerification.objects.update_or_create(
            user=self.context.get("user"), defaults=validated_data
        )
        return instance


class VerificationStatusSerializer(ModelSerializer):
    status_personal = CharField(source="personal_verification.status")
    status_address = CharField(source="address_verification.status")

    class Meta:
        model = User
        fields = [
            "status_personal",
            "status_address",
        ]
