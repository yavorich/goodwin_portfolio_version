from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.information.serializers import WalletSerializer
from apps.information.models import Wallet


class WalletAPIView(RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Wallet, user=self.request.user)
