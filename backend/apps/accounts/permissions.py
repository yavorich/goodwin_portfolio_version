from rest_framework.permissions import IsAuthenticated, BasePermission
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from config import settings


class IsAuthenticatedAndAcceptedOfferAgreement(IsAuthenticated):
    message = {
        "code": "offer_agreement_not_accepted",
        "detail": _(
            "Для доступа к этой странице необходимо принять условия договора оферты"
        ),
    }

    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.user.agreement_date is not None or request.user.business_account
        )


class IsAuthenticatedAndVerified(IsAuthenticatedAndAcceptedOfferAgreement):
    message = {
        "code": "user_not_verified",
        "detail": _(
            "Для доступа к этой странице необходимо подтвердить свою личность и адрес"
        ),
    }

    def has_permission(self, request, view):
        user: User = request.user
        self.message = super().message

        return super().has_permission(request, view) and (
            user.verified() or request.user.business_account
        )


class IsPartner(IsAuthenticatedAndVerified):
    message = {
        "code": "not_partner",
        "detail": _("Для доступа к этой странице необходимо иметь статус партнёра"),
    }

    def has_permission(self, request, view):
        user = request.user
        partner_profile = getattr(user, "partner_profile", None)
        if partner_profile is None:
            return False
        self.message = super().message
        return super().has_permission(request, view)


class IsLocal(BasePermission):
    message = {
        "code": "not_local",
        "detail": _(
            "Доступ к этой странице разрешён только для аутентифицированного "
            "локального приложения"
        ),
    }

    def has_permission(self, request, view):
        token = request.headers.get("X-Auth-Token")
        if token:
            return token == settings.LOCAL_TOKEN
        return False


class IsAdmin(IsAuthenticated):
    message = {
        "code": "not_admin",
        "detail": _("Действие доступно только администратору"),
    }

    def has_permission(self, request, view):
        token = view.kwargs.get("token")
        if not token:
            return False

        return (
            super().has_permission(request, view)
            and request.user.is_staff
            and token == settings.LOGIN_AS_USER_TOKEN
        )
