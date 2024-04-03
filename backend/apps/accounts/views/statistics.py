from datetime import timedelta
import pandas as pd

from django.db.models import (
    Sum,
    F,
    Window,
)
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, get_object_or_404, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.accounts.excel.statistics import TableStatisticsExcel
from apps.accounts.permissions import IsAuthenticatedAndVerified
from apps.accounts.serializers.statistics import (
    TotalProfitStatisticsGraphSerializer,
    GeneralInvestmentStatisticsSerializer,
    TableStatisticsSerializer,
)
from apps.accounts.services.statistics import (
    get_table_statistics,
    get_holiday_dates,
    get_table_total_statistics,
)
from apps.information.models import UserProgramAccrual, UserProgram
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


class TableStatisticsViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = TableStatisticsSerializer

    def get_queryset(self):
        user = self.request.user
        self.user_program = get_object_or_404(
            UserProgram, pk=self.kwargs.get("pk"), wallet=user.wallet
        )

        self.start_date, self.end_date = get_dates_range(
            UserProgramAccrual, self.request.query_params
        )
        accrual_results = get_table_statistics(
            self.start_date, self.end_date, self.user_program
        )
        return accrual_results

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def export(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        excel = TableStatisticsExcel()
        excel.to_excel(serializer.data)
        path = excel.save()
        response_data = {"url": self.request.build_absolute_uri(path)}
        return Response(response_data)

    @action(detail=True, methods=["get"])
    def total(self, request, *args, **kwargs):
        user = self.request.user
        user_program = get_object_or_404(
            UserProgram, pk=self.kwargs.get("pk"), wallet=user.wallet
        )

        start_date, end_date = get_dates_range(
            UserProgramAccrual, self.request.query_params
        )

        if not start_date and not end_date:
            return Response()

        totals = get_table_total_statistics(start_date, end_date, user_program)
        totals["total_trading_days"] = len(
            pd.bdate_range(
                start_date,
                end_date,
                freq="C",
                holidays=get_holiday_dates(start_date, end_date),
            ),
        )
        return Response(totals)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        week_days_list = [_("Вс"), _("Пн"), _("Вт"), _("Ср"), _("Чт"), _("Пт"), _("Сб")]

        context["holidays"] = get_holiday_dates(self.start_date, self.end_date)
        context["week_days_list"] = week_days_list
        return context
