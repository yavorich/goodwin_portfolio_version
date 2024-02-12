from decimal import Decimal

from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from apps.accounts.models.user import Partner, User
from apps.accounts.permissions import IsPartner
from apps.accounts.serializers.partner import (
    PartnerSerializer,
    PartnerTotalFeeSerializer,
)
from apps.information.models import Wallet


# from apps.accounts.serializers.partner import PartnerGeneralStatisticsSerializer


class PartnerGeneralStatisticsRetrieveView(RetrieveAPIView):
    permission_classes = [IsPartner]
    serializer_class = PartnerTotalFeeSerializer

    def get_object(self):
        user = self.request.user
        return user.partner_profile

    def retrieve(self, request, *args, **kwargs):
        partner_profile = self.get_object()

        investors = partner_profile.users.all()

        total_success_fee = (
            partner_profile.users.all()
            .annotate(
                user_total_success_fee=Sum("wallet__programs__accruals__success_fee")
            )
            .aggregate(total_success_fee=Sum("user_total_success_fee"))
        )["total_success_fee"]

        total_partner_fee = Decimal(total_success_fee) * partner_profile.partner_fee

        data = {
            "total_success_fee": total_success_fee,
            "total_partner_fee": total_partner_fee,
        }

        return Response(data)
        # return super().retrieve(request, *args, **kwargs)
