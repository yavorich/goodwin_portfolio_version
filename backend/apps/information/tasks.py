from celery import shared_task
from django.db import transaction
from django.utils.timezone import now, timedelta

from apps.information.models import (
    FrozenItem,
    Program,
    Operation,
    UserProgram,
    UserProgramReplenishment,
    ProgramResult,
)


@shared_task
def defrost_funds(pk):
    with transaction.atomic():
        items = FrozenItem.objects.filter(defrost_date=now().date())
        for item in items:
            item.defrost()


@shared_task
def apply_program_replenishments():
    with transaction.atomic():
        items = UserProgramReplenishment.objects.filter(
            status=UserProgramReplenishment.Status.INITIAL, apply_date=now().date()
        )
        for item in items:
            item.apply()


@shared_task
def apply_program_start():
    with transaction.atomic():
        items = UserProgram.objects.filter(
            status=UserProgram.Status.INITIAL, start_date=now().date()
        )
        for item in items:
            item.start()


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
        amount = user_program.funds * result.result / 100
        Operation.objects.create(
            type=Operation.Type.PROGRAM_ACCRUAL,
            wallet=user_program.wallet,
            amount=amount,
            confirmed=True,
        )
