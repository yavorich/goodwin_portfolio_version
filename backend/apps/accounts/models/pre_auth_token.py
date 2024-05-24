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

from apps.telegram.tasks import send_telegram_message_task
from config.settings import PRE_AUTH_CODE_EXPIRES, DEBUG
from .user import User


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

        pre_auth_token = self.filter(**filter_).order_by("-created_at").first()
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
            pre_auth_token = self.model(
                verify_type=verify_type,
                user=user,
                telegram_verify=(not has_telegram_confirmation),
                email_verify=(not has_email_confirmation),
            )
            pre_auth_token.send()
            return False, pre_auth_token.confirmation_data

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

    @property
    def confirmation_data(self):
        return {
            "token": self.token,
            "telegram": self._confirmation_telegram(),
            "email": self._confirmation_email(),
        }

    def _confirmation_telegram(self):
        if not self.telegram_verify:
            return self.user.telegram

    def _confirmation_email(self):
        if not self.email_verify:
            return self.user.email

    def send(self):
        from apps.accounts.services.email import send_confirmation_code_email
        from apps.accounts.models import EmailMessageType

        if not self.telegram_verify:
            self.telegram_code = self.generate_code()
            text = PRE_AUTH_TOKEN_TELEGRAM_TEXT[self.verify_type].format(
                code=self.telegram_code
            )
            send_telegram_message_task.delay(self.user.telegram_id, text)

        if not self.email_verify:
            self.email_code = self.generate_code()
            send_confirmation_code_email(
                self.user.email, self.email_code, EmailMessageType.AUTH_CONFIRM
            )

        self.save()


# данные email сообщений для всех типов подтверждения
PRE_AUTH_TOKEN_EMAIL_DATA = {
    PreAuthToken.VerifyType.AUTHORIZATION: {
        "title": _("Код подтверждения входа"),
        "description": _("Код подтверждения для входа в аккаунт: {code}"),
    },
}

# тексты telegram сообщений для всех типов подтверждения
PRE_AUTH_TOKEN_TELEGRAM_TEXT = {
    PreAuthToken.VerifyType.AUTHORIZATION: _(
        "Код подтверждения для входа в аккаунт: {code}"
    ),
}
