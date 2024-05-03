from django.urls import reverse

from apps.telegram.utils import send_telegram_message
from apps.telegram.models import AdminTelegramAccount
from config.settings import MAIN_URL


def send_admin_withdrawal_notifications(withdrawal_request):
    accounts = AdminTelegramAccount.objects.filter(telegram_id__isnull=False)

    admin_page_url = reverse(
        "admin:finance_withdrawalrequest_change",
        kwargs={"object_id": withdrawal_request.pk},
    )
    full_url = MAIN_URL + admin_page_url

    text = "Новая заявка на вывод средств: {}".format(full_url)
    for account in accounts:
        send_telegram_message(account.telegram_id, text)
