from django.utils.translation import gettext_lazy as _

from apps.accounts.tasks import send_email_msg
from apps.finance.models import OperationConfirmation


def send_operation_confirm_email(confirmation: OperationConfirmation):
    title = _("GOODWIN - Подтверждение операции")
    message = (
        _("Здравствуйте!\nВаш код для подтверждения операции")
        + f": {confirmation.code}"
    )
    send_email_msg.delay(
        confirmation.operation.wallet.user.email,
        title,
        message,
        from_email="GOODWIN",
        html=False,
    )
