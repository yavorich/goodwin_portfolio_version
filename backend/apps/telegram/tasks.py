from apps.telegram.utils import send_telegram_message
from apps.telegram.sender import send_template_telegram_message
from config.celery import celery_app


@celery_app.task
def send_telegram_message_task(user_telegram_id, text):
    send_telegram_message(user_telegram_id, text)


@celery_app.task
def send_template_telegram_message_task(
    telegram_id, message_type, insertion_data: dict | None = None, language=None
):
    send_template_telegram_message(telegram_id, message_type, insertion_data, language)
