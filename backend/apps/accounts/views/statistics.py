from datetime import datetime, timedelta

from django.db.models import Sum, F, Window
from rest_framework.generics import ListAPIView, get_object_or_404

from apps.accounts.permissions import IsAuthenticatedAndVerified
from apps.accounts.serializers.statistics import TotalProfitStatisticsGraphSerializer
from apps.information.models import WalletHistory, UserProgramAccrual, UserProgram


class TotalProfitStatisticsGraph(ListAPIView):
    permission_classes = [IsAuthenticatedAndVerified]
    serializer_class = TotalProfitStatisticsGraphSerializer

    def get_queryset(self):
        user_program_id = self.kwargs.get("program_id")
        user = self.request.user
        user_program = get_object_or_404(
            UserProgram, pk=user_program_id, wallet=user.wallet
        )

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if not start_date:
            start_date = WalletHistory.objects.earliest("created_at").created_at
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        if not end_date:
            end_date = WalletHistory.objects.latest("created_at").created_at
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        all_dates = [
            start_date + timedelta(days=x)
            for x in range((end_date - start_date).days + 1)
        ]

        results = (
            UserProgramAccrual.objects.filter(
                created_at__range=(start_date, end_date), program=user_program
            )
            .values("created_at", "amount")
            .order_by("created_at")
        )

        results = results.annotate(
            total_amount=Window(
                expression=Sum("amount"),
                order_by=F("created_at").asc(),
            )
        )

        results_dict = {entry["created_at"]: entry for entry in results}

        previous_total_amount = None
        final_results = []

        for date in all_dates:
            if date in results_dict:
                amount = results_dict[date]["amount"]
                previous_total_amount = results_dict[date]["total_amount"]
            else:
                amount = None
            final_results.append(
                {
                    "created_at": date,
                    "amount": amount,
                    "total_amount": previous_total_amount,
                }
            )

        return final_results
