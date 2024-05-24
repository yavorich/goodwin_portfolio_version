from uuid import uuid4
from django.utils import timezone, translation
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from config.settings import RECOVER_PASSWORD_CODE_EXPIRES, MAIN_URL
from apps.accounts.tasks import send_email_msg
from apps.accounts.models.email_message import EmailMessageType, EmailMessage
from core.utils.get_inserted_text import get_inserted_text


def get_template_message(message_type: EmailMessageType, insertion_data):
    template_message = EmailMessage.objects.get(message_type=message_type)
    language = translation.get_language()
    title = template_message.title.get(language)
    text = get_inserted_text(template_message, insertion_data, language)
    return title, text


def send_confirmation_code_email(email, code, message_type):
    title, text = get_template_message(message_type, insertion_data={"code": code})
    send_email_msg.delay(
        email,
        title,
        text,
        from_email="GOODWIN",
        html=False,
    )


def send_email_recover_password(user):
    code = uuid4()
    user.temp.changing_password_code = code
    user.temp.changing_password_code_expires = (
        timezone.now() + RECOVER_PASSWORD_CODE_EXPIRES
    )
    user.temp.save()
    title, text = get_template_message(
        EmailMessageType.PASSWORD_RECOVERY, insertion_data={"full_name": user.full_name}
    )

    message_template_context = {
        "confirmation_url": f"{MAIN_URL}/auth/new-password/{code}/",
        "title": title,
        "description": text,
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
