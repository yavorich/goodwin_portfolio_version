from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from rest_framework.generics import RetrieveAPIView, ListAPIView

from apps.accounts.models.user import Partner
from apps.accounts.permissions import IsPartner
from core.serializers.date_range import DateRangeSerializer
from apps.accounts.serializers.partner import (
    PartnerTotalFeeSerializer,
    InvestorsSerializer,
    PartnerInvestmentGraphSerializer,
    PartnerListSerializer,
)
from apps.information.models import UserProgram, WalletHistory
from core.pagination import PageNumberSetPagination
from core.utils.get_dates_range import get_dates_range


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
        )["total_success_fee"] or 0

        total_partner_fee = total_success_fee * partner_profile.partner_fee

        data = {
            "total_success_fee": total_success_fee or 0,
            "total_partner_fee": total_partner_fee or 0,
            "success_fee_percent": 0.3,  # TODO добавить обращение к Success fee
            "partner_fee_percent": partner_profile.partner_fee or 0,
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

        start_date, end_date = get_dates_range(WalletHistory, self.request.query_params)

        all_dates = [
            start_date + timedelta(days=x)
            for x in range((end_date - start_date).days + 1)
        ]

        results = (
            WalletHistory.objects.filter(
                created_at__range=(start_date, end_date), user__in=investors
            )
            .values("created_at")
            .annotate(total_sum=Sum("free") + Sum("frozen") + Sum("deposits"))
        )
        results_dict = {entry["created_at"]: entry for entry in results}
        final_results = [
            {
                "created_at": date,
                "total_sum": results_dict[date]["total_sum"]
                if date in results_dict
                else None,
            }
            for date in all_dates
        ]

        return final_results


class PartnerList(ListAPIView):
    serializer_class = PartnerListSerializer
    queryset = Partner.objects.all()
