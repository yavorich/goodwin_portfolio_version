import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
celery_app = Celery("config", broker=settings.CELERY_BROKER_URL)
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()

celery_app.conf.beat_schedule = {
    "create_wallet_history_daily": {
        "task": "apps.information.tasks.create_wallet_history",
        "schedule": crontab(hour="0", minute="20"),
    },
    "create_user_program_history_daily": {
        "task": "apps.information.tasks.create_user_program_history",
        "schedule": crontab(hour="0", minute="30"),
    },
    "delete_confirm_codes_daily": {
        "task": "apps.accounts.tasks.delete_confirm_codes",
        "schedule": crontab(hour="0", minute="10"),
    },
    "delete_settings_auth_codes_daily": {
        "task": "apps.accounts.tasks.delete_settings_auth_codes",
        "schedule": crontab(hour="0", minute="0"),
    },
}
