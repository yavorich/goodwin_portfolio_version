from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from apps.accounts.serializers import (
    RegisterUserSerializer,
    TokenObtainPairEmailConfirmSerializer,
)


class RegisterAPIView(CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        token_serializer = TokenObtainPairEmailConfirmSerializer(data=request.data)
        token_serializer.is_valid(raise_exception=True)
        return Response(
            data=token_serializer.validated_data, status=status.HTTP_201_CREATED
        )
