from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.serializers import TokenObtainPairEmailConfirmSerializer


class LoginAPIView(TokenObtainPairView):
    serializer_class = TokenObtainPairEmailConfirmSerializer
