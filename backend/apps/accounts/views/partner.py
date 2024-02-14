from datetime import timedelta, datetime
from decimal import Decimal

from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from rest_framework.generics import RetrieveAPIView, ListAPIView

from apps.accounts.permissions import IsPartner
from apps.accounts.serializers.partner import (
    PartnerTotalFeeSerializer,
    InvestorsSerializer,
    PartnerInvestmentGraphSerializer,
)
from apps.information.models import UserProgram, WalletHistory
from core.pagination import PageNumberSetPagination


class PartnerGeneralStatisticsRetrieveView(RetrieveAPIView):
    permission_classes = [IsPartner]
    serializer_class = PartnerTotalFeeSerializer

    def get_object(self):
        user = self.request.user
        partner_profile = user.partner_profile

        total_success_fee = (
            partner_profile.users.all()
            .annotate(
                user_total_success_fee=Sum("wallet__programs__accruals__success_fee")
            )
            .aggregate(total_success_fee=Sum("user_total_success_fee"))
        )["total_success_fee"]

        total_partner_fee = total_success_fee * partner_profile.partner_fee

        data = {
            "total_success_fee": total_success_fee or 0,
            "total_partner_fee": total_partner_fee or 0,
        }

        return data


class PartnerInvestorsList(ListAPIView):
    permission_classes = [IsPartner]
    serializer_class = InvestorsSerializer
    pagination_class = PageNumberSetPagination

    def get_queryset(self):
        user = self.request.user
        partner_profile = user.partner_profile
        queryset = partner_profile.users.all()

        queryset = queryset.annotate(
            total_funds=Coalesce(
                Sum(
                    "wallet__programs__funds",
                    filter=Q(wallet__programs__status=UserProgram.Status.RUNNING),
                ),
                Decimal(0.0),
            ),
        )

        queryset = queryset.annotate(
            total_net_profit=Coalesce(
                Sum("wallet__programs__accruals__amount"), Decimal(0.0)
            )
        )

        return queryset


class PartnerInvestmentGraph(ListAPIView):
    permission_classes = [IsPartner]
    serializer_class = PartnerInvestmentGraphSerializer

    def get_queryset(self):
        investors = self.request.user.partner_profile.users.all()

        start_date = WalletHistory.objects.earliest("created_at").created_at
        end_date = WalletHistory.objects.latest("created_at").created_at

        if start_date_string := self.request.query_params.get("start_date"):
            try:
                start_date = datetime.strptime(start_date_string, "%Y-%m-%d").date()
            except ValueError:
                pass

        if end_date_string := self.request.query_params.get("end_date"):
            try:
                end_date = datetime.strptime(end_date_string, "%Y-%m-%d").date()
            except ValueError:
                pass

        results = []

        current_date = start_date
        while current_date <= end_date:
            daily_totals = WalletHistory.objects.filter(
                created_at=current_date, user__in=investors
            ).aggregate(total_sum=Sum("free") + Sum("frozen") + Sum("deposits"))

            results.append(
                {
                    "date": current_date,
                    "total_amount": daily_totals["total_sum"] or 0,
                }
            )

            current_date += timedelta(days=1)

        return results
