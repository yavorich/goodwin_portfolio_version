from rest_framework.generics import RetrieveAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from django.shortcuts import get_object_or_404

from apps.information.serializers import (
    WalletSerializer,
    FrozenItemSerializer,
    OperationCreateSerializer,
)
from apps.information.models import Wallet, FrozenItem, Operation


class WalletAPIView(RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Wallet, user=self.request.user)


class FrozenItemViewSet(ModelViewSet):
    serializer_class = FrozenItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FrozenItem.objects.filter(
            wallet=self.request.user.wallet, status=FrozenItem.Status.INITIAL
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return FrozenItemSerializer
        return OperationCreateSerializer

    def get_extended_data(self):
        data = self.request.data.dict()
        data.update({
            "type": Operation.Type.DEFROST,
            "wallet": self.request.user.wallet,
        })
        return data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.get_extended_data())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(methods=["post"], detail=False)
    def defrost(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
