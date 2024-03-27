from django.utils.translation import gettext_lazy as _

from apps.information.models import Operation


def operation_replenishment_confirmation(operation: Operation, amount):
    if operation.amount > amount:
        return _("Insufficient amount transferred")

    if operation.amount == amount:
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
    operation._to_wallet()

    return message
