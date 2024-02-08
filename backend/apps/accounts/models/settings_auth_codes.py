from random import choice
from string import digits
from uuid import uuid4

from django.db.models import (
    Model,
    ForeignKey,
    CASCADE,
    UUIDField,
    CharField,
    DateTimeField,
    JSONField,
    TextChoices,
)

from apps.accounts.models import User


class DestinationType(TextChoices):
    EMAIL = "email"
    TELEGRAM = "telegram"


class SettingsAuthCodes(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name="auth_codes", null=True)
    token = UUIDField(default=uuid4, editable=False)
    auth_code = CharField(max_length=16)
    created_at = DateTimeField(auto_now_add=True)
    request_body = JSONField(default=dict)
    destination = CharField(choices=DestinationType.choices)

    @staticmethod
    def generate_code():
        return "".join((choice(digits) for i in range(10)))
