# flake8: noqa: F401

from .register import RegisterAPIView, RegisterConfirmView
from .login import LoginAPIView, LoginConfirmView, TokenRefreshAPIView
from .recover_password import RecoverPasswordAPIView, ResetPasswordAPIView
from .confirm_email import EmailConfirmAPIView
from .docs import DocsViewSet
from .profile import ProfileAPIView, PasswordChangeAPIView
