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
)
from apps.accounts.views.verification import VerificationAPIView

router = DefaultRouter()
router.register("docs", DocsViewSet, basename="docs")
# router.register("verification", VerificationViewSet, basename="verification")

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path(
        "login/confirm/<slug:service_type>/",
        LoginConfirmView.as_view(),
        name="login_confirm",
    ),
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
        VerificationAPIView.as_view(),
        name="verification",
    ),
    path(
        "profile/change_password/",
        PasswordChangeAPIView.as_view(),
        name="change-password",
    ),
] + router.urls
