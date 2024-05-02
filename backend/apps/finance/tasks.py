from celery import shared_task
from django.db import transaction
from django.db.models import Sum
from django.utils.timezone import now, localdate

from apps.accounts.models import User
from apps.finance.models import (
    FrozenItem,
    Program,
    Operation,
    UserProgram,
    UserProgramReplenishment,
    ProgramResult,
    WalletHistory,
    Wallet,
    Holidays,
)
from apps.finance.models.program import UserProgramHistory
from apps.finance.utils import create_accrual


@shared_task
def defrost_funds():
    with transaction.atomic():
        items = FrozenItem.objects.filter(
            status=FrozenItem.Status.INITIAL, defrost_date__lte=now().date()
        )
        for item in items:
            Operation.objects.create(
                type=Operation.Type.DEFROST,
                wallet=item.wallet,
                frozen_item=item,
                amount=item.amount,
            )


@shared_task
def apply_program_replenishments():
    with transaction.atomic():
        items = UserProgramReplenishment.objects.filter(
            status=UserProgramReplenishment.Status.INITIAL, apply_date__lte=now().date()
        )
        for item in items:
            item.status = UserProgramReplenishment.Status.DONE
            item.save()


@shared_task
def apply_program_start():
    with transaction.atomic():
        items = UserProgram.objects.filter(
            status=UserProgram.Status.INITIAL, start_date__lte=now().date()
        )
        for item in items:
            item.status = UserProgram.Status.RUNNING
            item.save()


@shared_task
def apply_program_finish():
    with transaction.atomic():
        items = UserProgram.objects.filter(end_date__isnull=False).filter(
            status=UserProgram.Status.RUNNING, end_date__lte=now().date()
        )
        for item in items:
            Operation.objects.create(
                type=Operation.Type.PROGRAM_CLOSURE,
                wallet=item.wallet,
                user_program=item,
                amount=item.funds,
            )


@shared_task
def make_daily_programs_accruals():
    with transaction.atomic():
        if Holidays.objects.filter(
            start_date__lte=localdate(), end_date__gte=localdate()
        ).exists():
            return "No accruals because of holiday"
        result = ProgramResult.objects.first()
        if not result:
            return "No program result found"
        programs = Program.objects.filter(accrual_type=Program.AccrualType.DAILY)
        for program in programs:
            make_program_accruals(program, result)
        result.save()


def make_program_accruals(program: Program, result: ProgramResult):
    user_programs = UserProgram.objects.filter(
        program=program, status=UserProgram.Status.RUNNING
    )
    for user_program in user_programs:
        if not user_program.accruals.filter(created_at=now().date()).exists():
            accrual = create_accrual(program, user_program, result)
            Operation.objects.create(
                type=Operation.Type.PROGRAM_ACCRUAL,
                wallet=user_program.wallet,
                user_program=user_program,
                amount=accrual.amount,
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


@shared_task
def create_user_program_history():
    users = User.objects.all()
    for user in users:
        wallet: Wallet = user.wallet
        for program in wallet.programs.all():
            UserProgramHistory.objects.create(
                user_program=program,
                funds=program.funds,
                deposit=program.deposit,
                profit=program.profit,
                status=program.status,
            )
