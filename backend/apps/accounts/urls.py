from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    DocsViewSet,
    PasswordChangeAPIView,
    ProfileAPIView,
    EmailConfirmAPIView,
    RecoverPasswordAPIView,
    ResetPasswordAPIView,
    LoginConfirmView,
    LoginAPIView,
    RegisterAPIView,
    TokenRefreshAPIView,
    RegisterConfirmView,
    LogoutAPIView,
    PartnerGeneralStatisticsRetrieveView,
)
from apps.accounts.views.partner import PartnerInvestorsList, PartnerInvestmentGraph
from apps.accounts.views.profile import SettingsAPIView, SettingsConfirmCreateView
from apps.accounts.views.verification import (
    VerificationAPIView,
    VerificationStatusAPIView,
)

router = DefaultRouter()
router.register("docs", DocsViewSet, basename="docs")

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("register/confirm/", RegisterConfirmView.as_view(), name="register_confirm"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path(
        "login/confirm/<slug:service_type>/",
        LoginConfirmView.as_view(),
        name="login_confirm",
    ),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path(
        "recover_password/send/",
        ResetPasswordAPIView.as_view(),
        name="reset-password",
    ),
    path(
        "recover_password/confirm/<token>/",
        RecoverPasswordAPIView.as_view(),
        name="recover-password",
    ),
    path("confirm_email/", EmailConfirmAPIView.as_view(), name="confirm-email"),
    path("profile/", ProfileAPIView.as_view(), name="profile"),
    path(
        "profile/verification/",
        VerificationStatusAPIView.as_view(),
        name="verification_status",
    ),
    path(
        "profile/verification/<verification_type>/",
        VerificationAPIView.as_view(),
        name="verification",
    ),
    path(
        "profile/change_password/",
        PasswordChangeAPIView.as_view(),
        name="change-password",
    ),
    path(
        "profile/settings/",
        SettingsAPIView.as_view(),
        name="settings",
    ),
    path(
        "profile/settings/confirm/<slug:destination>/",
        SettingsConfirmCreateView.as_view(),
        name="confirm-settings",
    ),
    path("refresh-token/", TokenRefreshAPIView.as_view(), name="refresh_token"),
    path(
        "partner/general/",
        PartnerGeneralStatisticsRetrieveView.as_view(),
        name="partner-general-statistics",
    ),
    path("partner/investors/", PartnerInvestorsList.as_view(), name="investors"),
    path("partner/investment/", PartnerInvestmentGraph.as_view(), name="investment"),
] + router.urls
