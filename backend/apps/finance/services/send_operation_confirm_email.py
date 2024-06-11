from apps.accounts.tasks import send_email_msg
from apps.accounts.models import EmailMessageType
from apps.accounts.services.email import get_template_message
from apps.finance.models.operation_confirmation import OperationConfirmation


def send_operation_confirm_email(confirmation: OperationConfirmation):
    title, text = get_template_message(
        message_type=EmailMessageType.OPERATION_CONFIRM,
        insertion_data={"code": confirmation.code},
    )
    send_email_msg.delay(
        confirmation.operation.wallet.user.email,
        title,
        text,
        from_email="GOODWIN",
        html=False,
    )
