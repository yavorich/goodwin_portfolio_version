from apps.information.models import (
    Program,
    UserProgram,
    ProgramResult,
    UserProgramAccrual,
)


def create_accrual(
    program: Program, user_program: UserProgram, result: ProgramResult
) -> UserProgramAccrual:
    amount = user_program.funds * result.result / 100
    management_fee = user_program.funds * program.management_fee / 100
    success_fee = max(0, amount * program.success_fee / 100)
    amount -= success_fee + management_fee
    return user_program.accruals.create(amount=amount, success_fee=success_fee)
