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

from apps.finance.models import UserProgramAccrual, Operation, Holidays
from apps.finance.models.program import (
    UserProgramHistory,
    UserProgram,
    UserProgramReplenishment,
)


def get_table_statistics(
    start_date: datetime.date, end_date: datetime.date, user_program: UserProgram
):
    program_history_subquery = UserProgramHistory.objects.filter(
        user_program=OuterRef("program"),
        created_at=OuterRef("created_at"),
    ).values("funds", "status")

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
        .annotate(total_amount=Coalesce(Sum("amount"), Decimal("0.0")))
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
            profitability=F("percent_amount"),
            withdrawal=Subquery(withdrawal_subquery),
            replenishment=Subquery(replenishment_subquery),
            status=Subquery(program_history_subquery.values("status")),
        )
        .order_by("created_at")
    )

    return accrual_results


def get_table_total_statistics(
    start_date: datetime.date, end_date: datetime.date, user_program: UserProgram
):
    accrual_results = get_table_statistics(start_date, end_date, user_program)
    user_program_history = (
        (
            UserProgramHistory.objects.filter(
                user_program=user_program,
                created_at=accrual_results.last()["created_at"],
            )
            .values("status")
            .first()
        )
        if accrual_results
        else None
    )

    last_program_status = (
        user_program_history["status"] if user_program_history else None
    )

    # Агрегация результатов
    totals = accrual_results.aggregate(
        total_funds=Sum("funds"),
        total_amount=Sum("amount"),
        total_percent_amount=Sum("percent_amount"),
        total_profitability=Sum("profitability"),
        total_success_fee=Sum("success_fee"),
        total_management_fee=Sum("management_fee"),
        total_replenishment=Sum("replenishment"),
        total_withdrawal=Sum("withdrawal"),
    )

    totals["last_program_status"] = last_program_status

    return totals


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


def get_branch_general_statistics(partner_profile):
    total_success_fee = (
        partner_profile.users.all()
        .annotate(user_total_success_fee=Sum("wallet__programs__accruals__success_fee"))
        .aggregate(total_success_fee=Sum("user_total_success_fee"))
    )["total_success_fee"] or 0

    total_partner_fee = total_success_fee * partner_profile.partner_fee

    data = {
        "total_success_fee": total_success_fee or 0,
        "total_partner_fee": total_partner_fee or 0,
        "success_fee_percent": 0.3,  # TODO добавить обращение к Success fee
        "partner_fee_percent": partner_profile.partner_fee or 0,
    }

    return data
