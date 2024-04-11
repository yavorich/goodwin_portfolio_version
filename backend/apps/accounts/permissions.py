from rest_framework.permissions import IsAuthenticated, BasePermission
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import (
    PersonalVerification,
    AddressVerification,
    VerificationStatus,
)
from config import settings


class IsAuthenticatedAndAcceptedOfferAgreement(IsAuthenticated):
    message = {
        "code": "offer_agreement_not_accepted",
        "detail": _(
            "Для доступа к этой странице необходимо принять условия договора оферты"
        ),
    }

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.agreement_date is not None
        )


class IsAuthenticatedAndVerified(IsAuthenticatedAndAcceptedOfferAgreement):
    message = {
        "code": "user_not_verified",
        "detail": _(
            "Для доступа к этой странице необходимо подтвердить свою личность и адрес"
        ),
    }

    def has_permission(self, request, view):
        user = request.user
        personal_verification: PersonalVerification = getattr(
            user, "personal_verification", None
        )
        address_verification: AddressVerification = getattr(
            user, "address_verification", None
        )

        if personal_verification is None or address_verification is None:
            return False

        self.message = super().message
        return (
            super().has_permission(request, view)
            and personal_verification.status == VerificationStatus.APPROVED
            and address_verification.status == VerificationStatus.APPROVED
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
