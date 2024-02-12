from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import RegisterConfirmation
from apps.accounts.serializers import RegisterUserSerializer, LoginConfirmSerializer


class RegisterAPIView(CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        confirmation_data = serializer.save()
        return Response(data=confirmation_data, status=status.HTTP_201_CREATED)


class RegisterConfirmView(GenericAPIView):
    serializer_class = LoginConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]
        token = serializer.validated_data["token"]

        user = RegisterConfirmation.objects.verify_code(token=token, code=code)
        refresh = RefreshToken.for_user(user)
        response_data = {
            "is_authenticated": True,
            "id": user.pk,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        return Response(response_data)
