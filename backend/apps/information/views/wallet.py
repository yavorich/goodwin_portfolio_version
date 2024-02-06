from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.information.serializers import WalletSerializer, FrozenItemSerializer
from apps.information.models import Wallet, FrozenItem


class WalletAPIView(RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Wallet, user=self.request.user)


class FrozenItemAPIView(ListAPIView):
    serializer_class = FrozenItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FrozenItem.objects.filter(wallet=self.request.user.wallet, done=False)
