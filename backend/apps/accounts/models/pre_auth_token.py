from random import choice
from string import digits
from uuid import uuid4

from django.db.models import (
    Model,
    UUIDField,
    DateTimeField,
    CharField,
    BooleanField,
    ForeignKey,
    TextChoices,
    CASCADE,
    Manager,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import NotFound, ParseError

from config.settings import PRE_AUTH_CODE_EXPIRES, DEBUG
from .user import User
from ..services import send_telegram_login_confirmation, send_email_login_confirmation


class PreAuthTokenManager(Manager):
    def verify_code(self, verify_type, service_type, token, code):
        if service_type == "telegram":
            verify_field = "telegram_verify"
            code_field = "telegram_code"
        elif service_type == "email":
            verify_field = "email_verify"
            code_field = "email_code"
        else:
            raise NotFound

        filter_ = {
            "verify_type": verify_type,
            "token": token,
            code_field: code,
            "created_at__gt": timezone.now() - PRE_AUTH_CODE_EXPIRES,
        }
        if DEBUG and code == "1" * 10:
            filter_.pop(code_field)

        pre_auth_token = self.filter().first()
        if pre_auth_token is None:
            raise ParseError(_("Неверный код"))

        setattr(pre_auth_token, verify_field, True)
        pre_auth_token.save()

        user = pre_auth_token.user
        if pre_auth_token.is_verify:
            pre_auth_token.delete()
            return user, True
        else:
            return user, False

    def send_code(self, verify_type, user):
        has_email_confirmation = user.settings.email_request_code_on_auth
        has_telegram_confirmation = (
            user.settings.telegram_request_code_on_auth and user.telegram is not None
        )

        if has_email_confirmation or has_telegram_confirmation:
            confirmation_data = {
                "telegram": None,
                "email": None,
            }
            pre_auth_token = self.model(
                verify_type=verify_type,
                user=user,
                telegram_verify=(not has_telegram_confirmation),
                email_verify=(not has_email_confirmation),
            )

            if has_telegram_confirmation:
                pre_auth_token.telegram_code = PreAuthToken.generate_code()
                # сделать универсальным для других типов подтверждения
                send_telegram_login_confirmation(
                    pre_auth_token.user, pre_auth_token.telegram_code
                )
                confirmation_data["telegram"] = user.telegram

            if has_email_confirmation:
                pre_auth_token.email_code = PreAuthToken.generate_code()
                # сделать универсальным для других типов подтверждения
                send_email_login_confirmation(
                    pre_auth_token.user, pre_auth_token.email_code
                )
                confirmation_data["email"] = user.email

            pre_auth_token.save()
            confirmation_data["token"] = pre_auth_token.token
            return False, confirmation_data

        return True, {}


class PreAuthToken(Model):
    class VerifyType(TextChoices):
        AUTHORIZATION = "authorization", "Авторизация"
        # добавить типы на для остальных проверок

    user = ForeignKey(User, on_delete=CASCADE)
    token = UUIDField(default=uuid4)
    verify_type = CharField(max_length=16, choices=VerifyType.choices)

    telegram_verify = BooleanField(default=False)
    email_verify = BooleanField(default=False)

    telegram_code = CharField(max_length=16)
    email_code = CharField(max_length=16)

    created_at = DateTimeField(auto_now_add=True)

    objects = PreAuthTokenManager()

    SERVICE_CODES = ("email", "telegram")

    @property
    def is_verify(self):
        return self.telegram_verify and self.email_verify

    @staticmethod
    def generate_code():
        return "".join((choice(digits) for i in range(10)))
