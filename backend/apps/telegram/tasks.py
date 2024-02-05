from apps.telegram.utils import send_telegram_message
from config.celery import celery_app


@celery_app.task
def send_telegram_message_task(user_telegram_id, text):
    send_telegram_message(user_telegram_id, text)
