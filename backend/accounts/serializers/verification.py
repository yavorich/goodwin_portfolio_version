from rest_framework.serializers import ModelSerializer, FileField
from accounts.models import (
    PersonalVerification,
    AddressVerification,
    VerificationStatus,
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
        validated_data["user"] = self.context.get("user")
        instance = PersonalVerification.objects.get_or_create(
            **validated_data, defaults={"status": VerificationStatus.CHECK}
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
        validated_data["user"] = self.context.get("user")
        instance = AddressVerification.objects.get_or_create(
            **validated_data, defaults={"status": VerificationStatus.CHECK}
        )
        return instance
