from datetime import timedelta
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
from django.utils import translation
from rest_framework.generics import ListAPIView, get_object_or_404, RetrieveAPIView

from apps.accounts.permissions import IsAuthenticatedAndVerified
from apps.accounts.serializers.statistics import (
    TotalProfitStatisticsGraphSerializer,
    GeneralInvestmentStatisticsSerializer,
    TableStatisticsSerializer,
)
from apps.information.models import UserProgramAccrual, UserProgram, Operation, Holidays
from apps.information.models.program import (
    UserProgramHistory,
    ProgramResult,
    UserProgramReplenishment,
)
from core.utils.get_dates_range import get_dates_range


class TotalProfitStatisticsGraph(ListAPIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = TotalProfitStatisticsGraphSerializer

    def get_queryset(self):
        user = self.request.user
        user_program = get_object_or_404(
            UserProgram, pk=self.kwargs.get("program_id"), wallet=user.wallet
        )

        start_date, end_date = get_dates_range(
            UserProgramAccrual, self.request.query_params
        )

        all_dates = [
            start_date + timedelta(days=x)
            for x in range((end_date - start_date).days + 1)
        ]

        results = (
            UserProgramAccrual.objects.filter(
                created_at__range=(start_date, end_date), program=user_program
            )
            .values("created_at", "amount", "percent_amount")
            .order_by("created_at")
        )

        results = results.annotate(
            percent_total_amount=Window(
                expression=Sum("percent_amount"),
                order_by=F("created_at").asc(),
            )
        )

        results_dict = {entry["created_at"]: entry for entry in results}

        previous_total_amount = None
        final_results = []

        for date in all_dates:
            if date in results_dict:
                amount = results_dict[date]["amount"]
                percent_amount = results_dict[date]["percent_amount"]
                previous_total_amount = results_dict[date]["percent_total_amount"]
            else:
                amount = None
                percent_amount = None
            final_results.append(
                {
                    "created_at": date,
                    "amount": amount,
                    "percent_amount": percent_amount,
                    "percent_total_amount": previous_total_amount,
                }
            )

        return final_results


class GeneralInvestmentStatisticsView(RetrieveAPIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = GeneralInvestmentStatisticsSerializer

    def get_object(self):
        user = self.request.user
        total_funds = (
            UserProgram.objects.filter(wallet=user.wallet)
            .exclude(status=UserProgram.Status.FINISHED)
            .aggregate(total_funds=Sum("funds"))["total_funds"]
            or 0
        )

        total_profits = (
            UserProgramAccrual.objects.filter(program__wallet=user.wallet).aggregate(
                total_profits=Sum("amount")
            )["total_profits"]
            or 0
        )
        try:
            start_date = UserProgram.objects.earliest("start_date").start_date
        except UserProgram.DoesNotExist:
            start_date = None

        return {
            "total_funds": total_funds,
            "total_profits": total_profits,
            "start_date": start_date,
        }


class TableStatisticsView(ListAPIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = TableStatisticsSerializer

    def get_queryset(self):
        user = self.request.user
        user_program = get_object_or_404(
            UserProgram, pk=self.kwargs.get("program_id"), wallet=user.wallet
        )

        self.start_date, self.end_date = get_dates_range(
            UserProgramAccrual, self.request.query_params
        )

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
                created_at__range=(self.start_date, self.end_date),
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        week_days = {
            "ru": ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"],
            "en": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            "cn": ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"],
        }
        week_days_list = week_days.get(translation.get_language(), week_days["en"])

        holidays = (
            Holidays.objects.filter(start_date__range=(self.start_date, self.end_date))
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

        context["holidays"] = holiday_dates
        context["week_days_list"] = week_days_list
        return context
