from decimal import Decimal
from django.utils.translation import gettext_lazy as _

from apps.information.models import Operation
from config.settings import DEBUG


def operation_replenishment_confirmation(operation: Operation, amount):
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
        operation.amount = amount

    operation.done = True
    operation.save()
    operation.wallet.update_balance(free=operation.amount * Decimal("0.985"))

    return message
