from random import choice
from string import digits

from django.db.models import (
    TextChoices,
    Model,
    ForeignKey,
    CharField,
    DateTimeField,
    CASCADE,
)

from apps.finance.models import Operation
from core.utils import blank_and_null


class DestinationType(TextChoices):
    EMAIL = "email"
    TELEGRAM = "telegram"


class OperationConfirmation(Model):
    operation = ForeignKey(Operation, related_name="confirmations", on_delete=CASCADE)
    destination = CharField(choices=DestinationType.choices)
    code = CharField(max_length=10, **blank_and_null)
    created_at = DateTimeField(auto_now_add=True)

    def generate_code(self):
        self.code = "".join((choice(digits) for i in range(6)))
        self.save()
