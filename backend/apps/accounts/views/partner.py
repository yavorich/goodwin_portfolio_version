from rest_framework.generics import RetrieveAPIView

from apps.accounts.models.user import Partner, User
from apps.accounts.permissions import IsPartner
from apps.accounts.serializers.partner import PartnerSerializer
from apps.information.models import Wallet


# from apps.accounts.serializers.partner import PartnerGeneralStatisticsSerializer


class PartnerGeneralStatisticsRetrieveView(RetrieveAPIView):
    permission_classes = [IsPartner]
    serializer_class = PartnerSerializer

    def get_object(self):
        user = self.request.user
        return user.partner_profile

    def retrieve(self, request, *args, **kwargs):
        partner_profile = self.get_object()

        investors = partner_profile.users.all()

        for investor in investors:
            wallet: Wallet = investor.wallet
            print(wallet.programs)

        return super().retrieve(request, *args, **kwargs)
