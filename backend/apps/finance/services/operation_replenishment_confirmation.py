from django.utils.translation import gettext_lazy as _

from apps.finance.models.operation_history import OperationHistory
from apps.finance.models.operation_type import MessageType, OperationType
from config.settings import DEBUG

from .commissions import add_commission_to_history


def operation_replenishment_confirmation(operation, amount):
    """Увеличивает баланс кошелька пользователя после подтверждения о получении суммы
    на криптокошелёк goodwin"""
    if operation.done:
        return _("Operation already done")
    if (operation.amount > amount) and not DEBUG:
        return _("Insufficient amount transferred")

    if (operation.amount == amount) or DEBUG:
        message = _(
            "The required amount has been transferred and credited to the account"
        )
    else:
        message = _(
            "More than the required amount has been transferred and credited to "
            "the account"
        )

        # пересчет комиссии и суммы с учетом комиссии
        operation.commission = operation.commission * (amount / operation.amount)
        operation.amount = amount
        operation.amount_net = operation.amount - operation.commission

    operation.wallet.update_balance(free=operation.amount_net)

    operation.done = True
    operation.save()

    operation.add_history(
        type=OperationHistory.Type.REPLENISHMENT,
        message_type=MessageType.REPLENISHMENT,
        target_name=operation.wallet.name,
        amount=operation.amount_net,
    )

    add_commission_to_history(
        commission_type=OperationType.REPLENISHMENT_FEE, amount=operation.commission
    )

    return message
