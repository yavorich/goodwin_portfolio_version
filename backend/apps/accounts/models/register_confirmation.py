from random import choice
from string import digits
from uuid import uuid4

from django.contrib.auth.hashers import make_password
from django.db.models import (
    Model,
    UUIDField,
    DateTimeField,
    CharField,
    EmailField,
    Manager,
    ForeignKey,
    CASCADE,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ParseError

from apps.accounts.services.email import send_confirmation_code_email
from config.settings import REGISTER_CONFIRMATION_EXPIRES, DEBUG
from core.utils import blank_and_null
from . import Partner
from .user import User
from .email_message import EmailMessageType


class RegisterConfirmationManager(Manager):
    def verify_code(self, token, code):
        filter_ = {
            "token": token,
            "code": code,
            "created_at__gt": timezone.now() - REGISTER_CONFIRMATION_EXPIRES,
        }
        if DEBUG and code == "1" * 10:
            filter_.pop("code")

        register_confirmation = self.filter(**filter_).order_by("-created_at").first()
        if register_confirmation is None:
            raise ParseError(_("Неверный код"))

        user = User.objects.create(**register_confirmation.user_data)
        self.filter(email=user.email).delete()
        return user

    def send_code(self, user_data):
        user_data["password"] = make_password(user_data["password"])
        register_confirmation = self.model(**user_data)
        register_confirmation.send()
        return register_confirmation.confirmation_data


class RegisterConfirmation(Model):
    token = UUIDField(default=uuid4)
    code = CharField(max_length=16)
    created_at = DateTimeField(auto_now_add=True)

    # user data
    email = EmailField("Электронная почта")
    first_name = CharField(_("first name"), max_length=150)
    last_name = CharField(_("last name"), max_length=150)
    partner = ForeignKey(
        Partner,
        verbose_name="Регион привязки",
        on_delete=CASCADE,
        **blank_and_null,
    )
    password = CharField(_("password"), max_length=128)

    objects = RegisterConfirmationManager()

    @staticmethod
    def generate_code():
        return "".join((choice(digits) for i in range(10)))

    @property
    def confirmation_data(self):
        return {
            "token": self.token,
            "email": self.email,
        }

    @property
    def user_data(self):
        return {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "partner": self.partner,
            "password": self.password,
        }

    def send(self):
        self.code = self.generate_code()
        send_confirmation_code_email(
            self.email, self.code, EmailMessageType.AUTH_CONFIRM
        )
        self.save()
