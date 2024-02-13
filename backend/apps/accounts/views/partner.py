from decimal import Decimal

from django.db.models import Sum, Q, Value
from django.db.models.functions import Coalesce
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from apps.accounts.permissions import IsPartner
from apps.accounts.serializers.partner import (
    PartnerTotalFeeSerializer,
    InvestorsSerializer,
)
from apps.information.models import UserProgram


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

        total_success_fee = Decimal(total_success_fee)

        total_partner_fee = total_success_fee * partner_profile.partner_fee

        data = {
            "total_success_fee": total_success_fee,
            "total_partner_fee": total_partner_fee,
        }

        return data


class PartnerInvestorsList(ListAPIView):
    permission_classes = [IsPartner]
    serializer_class = InvestorsSerializer
    pagination_class = LimitOffsetPagination

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
                Value(0.0),
            )
        )
        queryset = queryset.annotate(
            total_net_profit=Coalesce(
                Sum("wallet__programs__accruals__amount"), Value(0.0)
            )
        )

        return queryset
