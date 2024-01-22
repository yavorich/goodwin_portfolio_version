from rest_framework.serializers import ModelSerializer
from accounts.models import PersonalVerification, AddressVerification


class PersonalVerificationSerializer(ModelSerializer):
    class Meta:
        model = PersonalVerification
        fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "document_type",
            "document_issue_date",
            "file",
        ]
        extra_kwargs = {f: {"required": True} for f in fields}

    def create(self, validated_data):
        validated_data["user"] = self.context.get("user")
        return super().create(validated_data)


class AddressVerificationSerializer(ModelSerializer):
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
        return super().create(validated_data)
