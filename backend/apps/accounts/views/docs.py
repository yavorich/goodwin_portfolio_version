from django.utils import timezone
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.accounts.models import Docs
from apps.accounts.serializers import DocsSerializer


class DocsViewSet(ListModelMixin, GenericViewSet):
    queryset = Docs.objects.filter(document_type=Docs.Type.CONTRACT_OFFER)
    permission_classes = [IsAuthenticated]
    serializer_class = DocsSerializer

    def get_object(self):
        return get_object_or_404(Docs, document_type=Docs.Type.CONTRACT_OFFER)

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer_class()(instance=instance)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=False)
    def apply(self, request, *args, **kwargs):
        user = self.request.user
        if user.agreement_date is None:
            user.agreement_date = timezone.now()
            user.save()
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
