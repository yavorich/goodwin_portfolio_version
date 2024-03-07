import datetime
from decimal import Decimal

import pandas as pd
from django.db.models import (
    Sum,
    F,
    Window,
    OuterRef,
    Subquery,
    Func,
)
from django.db.models.functions import ExtractWeekDay, Coalesce

from apps.information.models import UserProgramAccrual, Operation, Holidays
from apps.information.models.program import (
    UserProgramHistory,
    UserProgram,
    ProgramResult,
    UserProgramReplenishment,
)


def get_table_statistics(
    start_date: datetime.date, end_date: datetime.date, user_program: UserProgram
):
    program_history_subquery = UserProgramHistory.objects.filter(
        user_program=OuterRef("program"),
        created_at=OuterRef("created_at"),
    ).values("funds", "status")

    program_subquery = UserProgram.objects.filter(pk=OuterRef("program_id")).values(
        "program"
    )
    program_result_subquery = ProgramResult.objects.filter(
        program=Subquery(program_subquery), created_at=OuterRef("created_at")
    ).values("result")

    replenishment_subquery = (
        UserProgramReplenishment.objects.filter(
            program=OuterRef("program"), created_at=OuterRef("created_at")
        )
        .annotate(total_amount=Coalesce(Func("amount", function="Sum"), Decimal(0)))
        .values("total_amount")
    )

    withdrawal_subquery = (
        Operation.objects.filter(
            user_program=OuterRef("program"),
            created_at__date=OuterRef("created_at"),
            type=Operation.Type.PROGRAM_CLOSURE,
        )
        .annotate(total_amount=Coalesce(Func("amount", function="Sum"), Decimal(0)))
        .values("total_amount")
    )

    accrual_results = (
        UserProgramAccrual.objects.filter(
            created_at__range=(start_date, end_date),
            program=user_program,
        )
        .values(
            "created_at",
            "amount",
            "percent_amount",
            "success_fee",
            "management_fee",
        )
        .annotate(
            percent_total_amount=Window(
                expression=Sum("percent_amount"),
                order_by=F("created_at").asc(),
            ),
            day_of_week=ExtractWeekDay("created_at"),
            funds=Subquery(program_history_subquery.values("funds")),
            profitability=Subquery(program_result_subquery),
            withdrawal=Subquery(withdrawal_subquery),
            replenishment=Subquery(replenishment_subquery),
            status=Subquery(program_history_subquery.values("status")),
        )
        .order_by("created_at")
    )

    return accrual_results


def get_holiday_dates(start_date, end_date):
    holidays = (
        Holidays.objects.filter(start_date__range=(start_date, end_date))
        .values("start_date", "end_date")
        .order_by("start_date")
    )

    holiday_dates = []
    for holiday in holidays:
        start_date = holiday["start_date"]
        end_date = holiday["end_date"]

        if end_date is None or start_date == end_date:
            holiday_dates.append(pd.Timestamp(start_date))
        else:
            date_range = pd.date_range(start_date, end_date).tolist()
            holiday_dates.extend(date_range)

    return holiday_dates
