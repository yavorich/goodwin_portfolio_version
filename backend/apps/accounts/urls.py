from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("docs", views.DocsViewSet, basename="docs")

urlpatterns = [
    path("register/", views.RegisterAPIView.as_view(), name="register"),
    path("login/", views.LoginAPIView.as_view(), name="login"),
    path(
        "login/confirm/<slug:service_type>/",
        views.LoginConfirmView.as_view(),
        name="login_confirm",
    ),
    path(
        "recover_password/send/",
        views.ResetPasswordAPIView.as_view(),
        name="reset-password",
    ),
    path(
        "recover_password/confirm/<token>/",
        views.RecoverPasswordAPIView.as_view(),
        name="recover-password",
    ),
    path("confirm_email/", views.EmailConfirmAPIView.as_view(), name="confirm-email"),
    path("profile/", views.ProfileAPIView.as_view(), name="profile"),
    path(
        "profile/verification/",
        views.VerificationAPIView.as_view(),
        name="verification",
    ),
    path(
        "profile/change_password/",
        views.PasswordChangeAPIView.as_view(),
        name="change-password",
    ),
] + router.urls
