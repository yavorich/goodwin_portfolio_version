# flake8: noqa: F401

from .register import RegisterAPIView
from .login import LoginAPIView
from .recover_password import RecoverPasswordAPIView, ResetPasswordAPIView
from .confirm_email import EmailConfirmAPIView
from .docs import DocsViewSet
from .verification import VerificationAPIView
from .profile import ProfileAPIView
