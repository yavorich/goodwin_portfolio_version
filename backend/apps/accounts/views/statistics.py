from datetime import timedelta

from django.db.models import Sum, F, Window
from rest_framework.generics import ListAPIView, get_object_or_404, RetrieveAPIView

from apps.accounts.permissions import IsAuthenticatedAndVerified
from apps.accounts.serializers.date_range import DateRangeSerializer
from apps.accounts.serializers.statistics import (
    TotalProfitStatisticsGraphSerializer,
    GeneralInvestmentStatisticsSerializer,
)
from apps.information.models import UserProgramAccrual, UserProgram


class TotalProfitStatisticsGraph(ListAPIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = TotalProfitStatisticsGraphSerializer

    def get_queryset(self):
        user_program_id = self.kwargs.get("program_id")
        user = self.request.user
        user_program = get_object_or_404(
            UserProgram, pk=user_program_id, wallet=user.wallet
        )

        serializer = DateRangeSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data.get(
            "start_date", UserProgramAccrual.objects.earliest("created_at").created_at
        )
        end_date = serializer.validated_data.get(
            "end_date", UserProgramAccrual.objects.latest("created_at").created_at
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

        print(
            {
                "total_funds": total_funds,
                "total_profits": total_profits,
                "start_date": start_date,
            }
        )
        return {
            "total_funds": total_funds,
            "total_profits": total_profits,
            "start_date": start_date,
        }
