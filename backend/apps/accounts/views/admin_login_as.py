from django.conf import settings
from django.http.response import HttpResponseRedirect, Http404
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404

from django.views import View

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.models import User
from apps.accounts.permissions import IsAdmin
from config.settings import FRONT_URL


class LoginAsUserView(View):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        self.check_permissions()

        user = get_object_or_404(User, pk=self.kwargs["pk"])
        response = HttpResponseRedirect(redirect_to=FRONT_URL)
        refresh = RefreshToken.for_user(user)
        response.set_cookie("refresh_token", str(refresh))
        response.set_cookie("access_token", str(refresh.access_token))
        response.set_cookie("csrftoken", str(get_token(request)))
        response.set_cookie(settings.SESSION_COOKIE_NAME, request.session.session_key)
        return response

    def check_permissions(self):
        if not all(
            (
                permission_class().has_permission(self.request, self)
                for permission_class in self.permission_classes
            )
        ):
            raise Http404
