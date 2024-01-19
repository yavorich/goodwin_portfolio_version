from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager

from core.utils import blank_and_null
from .region import Region


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users require an email field")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(_("Email address"), unique=True)
    email_is_confirmed = models.BooleanField(default=False)
    region = models.ForeignKey(
        Region,
        verbose_name=_("Region"),
        related_name="users",
        on_delete=models.CASCADE,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    @property
    def full_name(self):
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"


class TempData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="temp")

    email_verify_code = models.CharField(
        "Код для подтверждения почты", **blank_and_null
    )
    email_verify_code_expires = models.DateTimeField(**blank_and_null)
    email_last_sending_code = models.DateTimeField(**blank_and_null)

    changing_password_code = models.UUIDField("Код для смены пароля", **blank_and_null)
    changing_password_code_expires = models.DateTimeField(
        "Время истечения кода", **blank_and_null
    )

    class Meta:
        verbose_name = "Коды подтверждения пользователя"
        verbose_name_plural = "Коды подтверждения пользователей"

    def __str__(self):
        return f"{self.user}"
