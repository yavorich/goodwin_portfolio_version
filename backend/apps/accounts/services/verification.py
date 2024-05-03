from django.urls import reverse

from apps.telegram.utils import send_telegram_message
from apps.telegram.models import AdminTelegramAccount

from apps.accounts.models import User
from config.settings import MAIN_URL


def send_admin_verify_notifications(user: User, verification_type: str):
    accounts = AdminTelegramAccount.objects.filter(telegram_id__isnull=False)
    sample = {
        "personal": "личности",
        "address": "адреса",
    }
    admin_page_url = reverse(
        "admin:accounts_user_change", kwargs={"object_id": user.pk}
    )
    full_url = MAIN_URL + admin_page_url
    text = "Новый запрос на верификацию {}: {}".format(
        sample[verification_type], full_url
    )
    for account in accounts:
        send_telegram_message(account.telegram_id, text)
