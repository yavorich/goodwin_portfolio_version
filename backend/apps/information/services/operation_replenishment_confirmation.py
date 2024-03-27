from django.utils.translation import gettext_lazy as _

from apps.information.models import Operation


def operation_replenishment_confirmation(operation: Operation, amount):
    """Увеличивает баланс кошелька пользователя после подтверждения о получении суммы
    на криптокошелёк goodwin"""
    if operation.amount > amount:
        message = _("Insufficient amount transferred")
    elif operation.amount == amount:
        message = _(
            "The required amount has been transferred and credited to the account"
        )
        operation._to_wallet()
    else:
        message = _(
            "More than the required amount has been transferred and credited to "
            "the account"
        )
        operation.amount = amount
        operation.save()
        operation._to_wallet()

    return message
