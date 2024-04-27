from django.http.response import HttpResponseRedirect

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.models import User
from apps.accounts.permissions import IsAdmin
from config.settings import FRONT_URL


class LoginAsUserView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, *args, **kwargs):
        user = User.objects.get(pk=self.kwargs["pk"])
        response = HttpResponseRedirect(redirect_to=FRONT_URL)
        refresh = str(RefreshToken.for_user(user))
        access = str(AccessToken.for_user(user))
        response["Cookie"] = f"access={access};refresh={refresh}"
        return response
