from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import RetrieveAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import IsAuthenticatedAndVerified
from apps.finance.serializers import (
    WalletSerializer,
    FrozenItemSerializer,
    wallet_operations_serializers,
    WalletTransferUserSerializer,
)
from apps.finance.models import Wallet, FrozenItem
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


class WalletTransferAPIView(GenericAPIView):
    permission_classes = [IsAuthenticatedAndVerified]

    def post(self, request, *args, **kwargs):
        serializer = WalletTransferUserSerializer(
            data=request.data, context={"user": self.request.user}
        )
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data, status=HTTP_200_OK)
