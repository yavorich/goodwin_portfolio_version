from apps.finance.models import (
    UserProgram,
    ProgramResult,
    UserProgramAccrual,
)

from apps.finance.services import get_commission_pct
from core.utils import safe_zero_div


def create_accrual(
    user_program: UserProgram, result: ProgramResult
) -> UserProgramAccrual:
    success_fee_pct = get_commission_pct(user_program.wallet, "success_fee")
    management_fee_pct = get_commission_pct(user_program.wallet, "management_fee")

    amount = user_program.funds * result.result / 100
    management_fee = user_program.deposit * management_fee_pct / 100
    success_fee = max(0, amount * success_fee_pct / 100)

    amount -= success_fee + management_fee
    percent_amount = safe_zero_div(amount * 100, user_program.funds)

    return user_program.accruals.create(
        amount=amount,
        percent_amount=percent_amount,
        success_fee=success_fee,
        management_fee=management_fee,
    )
