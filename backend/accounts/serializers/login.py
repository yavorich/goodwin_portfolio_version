from typing import Dict, Any

from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.services import send_email_confirmation


class TokenObtainPairEmailConfirmSerializer(TokenObtainPairSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        data = super(TokenObtainPairSerializer, self).validate(attrs)
        data["id"] = self.user.id

        refresh = self.get_token(self.user)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        send_email_confirmation(self.user)
        update_last_login(None, self.user)

        return data
