from random import choice
from string import digits

from django.contrib.auth import get_user_model
from django.db.models import (
    CharField,
    Model,
    OneToOneField,
    Manager,
    CASCADE,
)

User = get_user_model()


class MessengerCodeManager(Manager):
    def generate(self, user):
        code = "".join((choice(digits) for i in range(6)))
        if hasattr(user, "confirmationcode"):
            confirmation_code = user.confirmationcode
            confirmation_code.code = code
            confirmation_code.save()
            return confirmation_code

        return self.create(user=user, code=code)


class ConfirmationCode(Model):
    user = OneToOneField(User, on_delete=CASCADE)
    code = CharField(
        max_length=6,
        verbose_name="Код",
    )
    objects = MessengerCodeManager()
