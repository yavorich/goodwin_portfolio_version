from django.utils.translation import gettext_lazy as _

from apps.accounts.tasks import send_email_msg
from apps.finance.models import Operation


def send_operation_confirm_email(operation: Operation):
    title = _("GOODWIN - Подтверждение операции")
    message = (
        _(f'Здравствуйте!\nВаш код для подтверждения операции "{operation}"')
        + f": {operation.confirmation_code}"
    )
    send_email_msg.delay(
        operation.wallet.user.email,
        title,
        message,
        from_email="GOODWIN",
        html=False,
    )
