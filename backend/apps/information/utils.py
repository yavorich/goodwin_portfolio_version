from apps.information.models import Program, UserProgram, ProgramResult


def get_accrual_amount(
    program: Program, user_program: UserProgram, result: ProgramResult
):
    amount = user_program.funds * (result.result - program.management_fee) / 100
    if amount > 0:
        amount *= (1 - program.success_fee / 100)
    return amount
