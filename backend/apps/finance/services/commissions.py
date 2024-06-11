from django.utils.timezone import now

from apps.finance.models.operation_history import OperationHistory
from apps.finance.models.operation_type import OperationType
from apps.finance.models.wallet import Wallet


def add_commission_to_history(commission_type: OperationType, amount):
    wallet = Wallet.objects.get(user__business_account=True)
    commission = OperationHistory.objects.filter(
        wallet=wallet, operation_type=commission_type, created_at__date=now().date()
    ).first()
    if commission:
        commission.amount += amount
        commission.save()
    else:
        commission = OperationHistory.objects.create(
            wallet=wallet,
            type=OperationHistory.Type.SYSTEM_MESSAGE,
            operation_type=commission_type,
            created_at=now(),
            amount=amount,
            is_commission=True,
        )
    wallet.update_balance(free=amount)
