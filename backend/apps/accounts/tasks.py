from celery import shared_task
from celery.schedules import crontab
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.html import strip_tags

from config import celery_app
from config.settings import (
    EMAIL_HOST_USER,
    PRE_AUTH_CODE_EXPIRES,
    CHANGE_SETTINGS_CODE_EXPIRES,
)
from apps.accounts.models import PreAuthToken, SettingsAuthCodes


@shared_task
def send_email_msg(email, subject, msg, from_email=None, html=False):
    if from_email is None:
        from_email = EMAIL_HOST_USER
    else:
        from_email = f"{from_email} <{EMAIL_HOST_USER}>"

    msg_data = {
        "subject": subject,
        "from_email": from_email,
        "recipient_list": [email],
    }
    if html:
        msg_data["message"] = strip_tags(msg)
        msg_data["html_message"] = msg
    else:
        msg_data["message"] = msg

    return send_mail(**msg_data)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=0, minute=10),
        delete_confirm_codes.s(),
    )


@celery_app.task
def delete_confirm_codes():
    PreAuthToken.objects.filter(
        created_at__lt=timezone.now() - PRE_AUTH_CODE_EXPIRES
    ).delete()


@celery_app.task
def delete_settings_auth_codes():
    SettingsAuthCodes.objects.filter(
        created_at__lt=timezone.now() - CHANGE_SETTINGS_CODE_EXPIRES
    ).delete()
