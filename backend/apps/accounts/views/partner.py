from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, OuterRef, Subquery
from django.db.models.functions import Coalesce
from rest_framework.generics import RetrieveAPIView, ListAPIView, get_object_or_404

from apps.accounts.models.user import Partner, VerificationStatus
from apps.accounts.permissions import IsPartner
from apps.finance.serializers import UserProgramSerializer
from apps.accounts.serializers.partner import (
    PartnerTotalFeeSerializer,
    InvestorsSerializer,
    PartnerInvestmentGraphSerializer,
    PartnerListSerializer,
)
from apps.finance.models import UserProgram, WalletHistory, UserProgramAccrual
from apps.accounts.services.statistics import get_branch_general_statistics
from core.pagination import PageNumberSetPagination
from core.utils.get_dates_range import get_dates_range


class PartnerGeneralStatisticsRetrieveView(RetrieveAPIView):
    permission_classes = [IsPartner]
    serializer_class = PartnerTotalFeeSerializer

    def get_object(self):
        user = self.request.user
        partner_profile = user.partner_profile

        data = get_branch_general_statistics(partner_profile)
        return data


class PartnerInvestorsList(ListAPIView):
    permission_classes = [IsPartner]
    serializer_class = InvestorsSerializer
    pagination_class = PageNumberSetPagination

    def get_queryset(self):
        user = self.request.user
        partner_profile = user.partner_profile
        queryset = partner_profile.users.filter(
            personal_verification__status=VerificationStatus.APPROVED,
            address_verification__status=VerificationStatus.APPROVED,
        ).all()

        total_funds_subquery = Subquery(
            UserProgram.objects.filter(
                wallet=OuterRef("wallet"), status=UserProgram.Status.RUNNING
            )
            .values("wallet")
            .annotate(total_funds=Sum("funds"))
            .values("total_funds"),
        )
        total_accruals_subquery = Subquery(
            UserProgramAccrual.objects.filter(
                program__wallet=OuterRef("wallet"),
                program__status=UserProgram.Status.RUNNING,
            )
            .values("program__wallet")
            .annotate(total_amount=Sum("amount"))
            .values("total_amount"),
        )

        queryset = queryset.annotate(
            total_funds=Coalesce(total_funds_subquery, Decimal("0.0")),
            total_net_profit=Coalesce(total_accruals_subquery, Decimal("0.0")),
        )

        return queryset


class PartnerInvestorPrograms(ListAPIView):
    permission_classes = [IsPartner]
    serializer_class = UserProgramSerializer

    def get_queryset(self):
        user = self.request.user
        partner_profile = user.partner_profile
        investors = partner_profile.users.all()
        investor = get_object_or_404(investors, pk=self.kwargs["pk"])
        return investor.wallet.programs.all()


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
                "total_sum": (
                    results_dict[date]["total_sum"] if date in results_dict else None
                ),
            }
            for date in all_dates
        ]

        return final_results


class PartnerList(ListAPIView):
    serializer_class = PartnerListSerializer
    queryset = Partner.objects.all()
