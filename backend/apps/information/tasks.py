from celery import shared_task
from django.db import transaction
from django.db.models import Sum
from django.utils.timezone import now, timedelta

from apps.accounts.models import User
from apps.information.models import (
    FrozenItem,
    Program,
    Operation,
    UserProgram,
    UserProgramReplenishment,
    ProgramResult,
    WalletHistory,
    Wallet,
)
from apps.information.utils import create_accrual


@shared_task
def defrost_funds(pk):
    with transaction.atomic():
        items = FrozenItem.objects.filter(defrost_date=now().date())
        for item in items:
            Operation.objects.create(
                type=Operation.Type.DEFROST,
                wallet=item.wallet,
                frozen_item=item,
                amount=item.amount,
                confirmed=True,
            )


@shared_task
def apply_program_replenishments():
    with transaction.atomic():
        items = UserProgramReplenishment.objects.filter(
            status=UserProgramReplenishment.Status.INITIAL, apply_date=now().date()
        )
        for item in items:
            item.operation._to_program()


@shared_task
def apply_program_start():
    with transaction.atomic():
        items = UserProgram.objects.filter(
            status=UserProgram.Status.INITIAL, start_date=now().date()
        )
        for item in items:
            item.start()


@shared_task
def apply_program_finish():
    with transaction.atomic():
        items = UserProgram.objects.filter(end_date=now().date(), force_closed=False)
        for item in items:
            item.close(force=False)


@shared_task
def make_daily_programs_accruals():
    with transaction.atomic():
        programs = Program.objects.filter(accrual_type=Program.AccrualType.DAILY)
        for program in programs:
            make_program_accruals(program)


def make_program_accruals(program):
    result = program.results.latest() or ProgramResult.objects.latest(
        program__isnull=True
    )
    if not result or result.created_at < now() - timedelta(days=1):
        result = ProgramResult.objects.create()

    user_programs = program.users.filter(status=UserProgram.Status.RUNNING)
    for user_program in user_programs:
        accrual = create_accrual(program, user_program, result)
        Operation.objects.create(
            type=Operation.Type.PROGRAM_ACCRUAL,
            wallet=user_program.wallet,
            accrual=accrual,
            amount=accrual.amount,
            confirmed=True,
        )


@shared_task
def create_wallet_history():
    users = User.objects.all()

    for user in users:
        wallet: Wallet = user.wallet
        total_funds = (
            UserProgram.objects.filter(
                wallet=wallet,
            )
            .exclude(status=UserProgram.Status.FINISHED)
            .aggregate(total_funds=Sum("funds"))["total_funds"]
            or 0
        )

        WalletHistory.objects.create(
            user=user, free=wallet.free, frozen=wallet.frozen, deposits=total_funds
        )
