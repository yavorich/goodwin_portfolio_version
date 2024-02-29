from datetime import timedelta, datetime
from decimal import Decimal

from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response

from apps.accounts.filters.wallet_history import WalletHistoryFilter
from apps.accounts.models.user import Partner
from apps.accounts.permissions import IsPartner
from apps.accounts.serializers.partner import (
    PartnerTotalFeeSerializer,
    InvestorsSerializer,
    PartnerInvestmentGraphSerializer,
    PartnerListSerializer,
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
    filterset_class = WalletHistoryFilter

    def get_queryset(self):
        investors = self.request.user.partner_profile.users.all()

        start_date = WalletHistory.objects.earliest("created_at").created_at
        end_date = WalletHistory.objects.latest("created_at").created_at

        results = (
            WalletHistory.objects.filter(
                created_at__range=(start_date, end_date), user__in=investors
            )
            .values("created_at")
            .annotate(total_sum=Sum("free") + Sum("frozen") + Sum("deposits"))
        )

        return results

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

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

        results_dict = {item["created_at"]: item["total_sum"] for item in queryset}

        for date in all_dates:
            if date not in results_dict:
                results_dict[date] = None

        response_data = [
            {"created_at": date, "total_sum": total_sum}
            for date, total_sum in sorted(results_dict.items())
        ]

        return Response(response_data)


class PartnerList(ListAPIView):
    serializer_class = PartnerListSerializer
    queryset = Partner.objects.all()
