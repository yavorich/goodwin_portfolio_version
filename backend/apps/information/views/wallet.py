from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from apps.information.serializers import (
    WalletSerializer,
    FrozenItemSerializer,
    wallet_operations_serializers,
)
from apps.information.models import Wallet, FrozenItem
from core.views import OperationViewMixin


class WalletAPIView(RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Wallet, user=self.request.user)


class WalletViewSet(OperationViewMixin, ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Wallet, user=self.request.user)

    def get_serializer_class(self):
        return wallet_operations_serializers[self.action]

    @action(methods=["post"], detail=False)
    def transfer(self, *args, **kwargs):
        return self.create(*args, **kwargs)

    @action(methods=["post"], detail=False)
    def withdraw(self, *args, **kwargs):
        return self.create(*args, **kwargs)

    @action(methods=["post"], detail=False)
    def replenish(self, *args, **kwargs):
        return self.create(*args, **kwargs)


class FrozenItemViewSet(OperationViewMixin, ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FrozenItem.objects.filter(
            wallet=self.request.user.wallet, status=FrozenItem.Status.INITIAL
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return FrozenItemSerializer
        return wallet_operations_serializers[self.action]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(methods=["post"], detail=False)
    def defrost(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
