import random
from uuid import uuid4
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from config.settings import RECOVER_PASSWORD_CODE_EXPIRES, MAIN_URL
from apps.accounts.tasks import send_email_msg


def send_auth_confirm_email(user):
    if user.temp.email_last_sending_code is None:
        pass
    elif (
        user.temp.email_last_sending_code + timezone.timedelta(minutes=1)
        > timezone.now()
    ):
        return

    code = "".join([str(random.randint(0, 9)) for i in range(6)])
    user.temp.email_verify_code = code
    user.temp.email_last_sending_code = timezone.now()
    user.temp.save()
    title = _("GOODWIN - Подтверждение электронной почты")
    message = _("Здравствуйте!\nВаш код для подтверждения почты") + f": {code}"
    send_email_msg.delay(
        user.email,
        title,
        message,
        from_email="GOODWIN",
        html=False,
    )


def send_email_recover_password(user, request):
    code = uuid4()
    user.temp.changing_password_code = code
    user.temp.changing_password_code_expires = (
        timezone.now() + RECOVER_PASSWORD_CODE_EXPIRES
    )
    user.temp.save()

    message_template_context = {
        "confirmation_url": f"{MAIN_URL}/auth/new-password/{code}/",
        "title": _("Восстановление пароля"),
        "description": _(
            "Здравствуйте, {full_name}!\n"
            "Был отправлен запрос на сброс пароля для вашего аккаунта. "
            "Если это сделали не вы, проигнорируйте данное сообщение "
            "(Эта ссылка действует 1 раз и в течение 24 часов)"
        ).format(full_name=user.full_name),
        "text_button": _("Сбросить пароль"),
    }
    html_message = render_to_string("email_message.html", message_template_context)
    send_email_msg.delay(
        user.email,
        message_template_context["title"],
        html_message,
        from_email="GOODWIN",
        html=True,
    )


def send_email_change_settings(user, code):
    message = _("Здравствуйте!\nВаш код для подтверждения смены настроек") + f": {code}"
    send_email_msg.delay(
        email=user.email,
        subject=_("GOODWIN - Смена настроек"),
        msg=message,
        from_email="GOODWIN",
        html=False,
    )


def send_email_change_password(user, code):
    message = _("Здравствуйте!\nВаш код для подтверждения смены пароля") + f": {code}"
    send_email_msg.delay(
        email=user.email,
        subject=_("GOODWIN - Смена пароля"),
        msg=message,
        from_email="GOODWIN",
        html=False,
    )


def send_email_change_email(email, code):
    message = (
        _("Здравствуйте!\nВаш код для подтверждения смены адреса электронной почты")
        + f": {code}"
    )
    send_email_msg.delay(
        email=email,
        subject=_("GOODWIN - Смена адреса электронной почты"),
        msg=message,
        from_email="GOODWIN",
        html=False,
    )
