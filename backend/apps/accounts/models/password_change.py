from uuid import uuid4
from random import choice
from string import digits
from django.db.models import (
    Model,
    ForeignKey,
    CharField,
    DateTimeField,
    UUIDField,
    CASCADE,
)

from apps.accounts.models import User


class PasswordChangeConfirmation(Model):
    user = ForeignKey(
        User, on_delete=CASCADE, related_name="password_confirmation", null=True
    )
    token = UUIDField(default=uuid4, editable=False)
    auth_code = CharField(max_length=16)
    created_at = DateTimeField(auto_now_add=True)
    new_password = CharField(max_length=128)

    @staticmethod
    def generate_code():
        return "".join((choice(digits) for i in range(10)))
