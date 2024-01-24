import os
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
        user = self._create_user(email, password, **extra_fields)
        Settings.objects.create(user=user)
        return user

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
    agreement_applied = models.BooleanField(default=False)
    region = models.ForeignKey(
        Region,
        verbose_name=_("Region"),
        related_name="users",
        on_delete=models.CASCADE,
        **blank_and_null
    )
    telegram = models.CharField(_("Telegram"), max_length=127, blank=True, null=True)
    inviter = models.ForeignKey(
        "User",
        verbose_name=_("Inviter"),
        related_name="invited_users",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    @property
    def full_name(self):
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"


class Settings(models.Model):
    user = models.OneToOneField(User, related_name="settings", on_delete=models.CASCADE)
    email_request_code_on_auth = models.BooleanField(default=True)
    email_request_code_on_withdrawal = models.BooleanField(default=True)
    telegram_request_code_on_auth = models.BooleanField(default=True)
    telegram_request_code_on_withdrawal = models.BooleanField(default=False)


def get_id_doc_upload_path(instance, filename):
    return os.path.join("users", "id", str(instance.user.pk), filename)


def get_addr_doc_upload_path(instance, filename):
    return os.path.join("users", "address", str(instance.user.pk), filename)


class VerificationStatus(models.TextChoices):
    NO_DATA = "no_data", _("No data")
    CHECK = "check", _("Check")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")


class PersonalVerification(models.Model):
    class DocumentType(models.TextChoices):
        PASSPORT = "passport", _("Passport")
        ID_CARD = "id_card", _("ID card")
        DRIVER_LICENSE = "driver_license", _("Driver's license")
        RESIDENCE_PERMIT = "residence_permit", _("Residence permit")

    class Gender(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")

    user = models.OneToOneField(
        User, related_name="personal_verification", on_delete=models.CASCADE
    )
    first_name = models.CharField(_("First name"), max_length=255)
    last_name = models.CharField(_("Last name"), max_length=255)
    gender = models.CharField(_("Gender"), choices=Gender.choices)
    date_of_birth = models.DateField(_("Date of birth"))
    document_type = models.CharField(_("Document type"), choices=DocumentType.choices)
    document_issue_date = models.DateField(_("Document issue date"))
    document_issue_region = models.CharField(
        _("Document issue region/country"), max_length=255
    )
    file = models.FileField(_("File"), upload_to=get_id_doc_upload_path)
    status = models.CharField(
        _("Status"),
        choices=VerificationStatus.choices,
        default=VerificationStatus.NO_DATA,
    )


class AddressVerification(models.Model):
    class DocumentType(models.TextChoices):
        REGISTRATION = "registration", _("Passport registration")
        UTILITY_BILL = "utility_bill", _("Utility bill")
        BANK_STATEMENT = "bank_statement", _("Bank statement")
        OTHER = "other", _("Other document")

    user = models.OneToOneField(
        User, related_name="address_verification", on_delete=models.CASCADE
    )
    country = models.CharField(_("Country"), max_length=255)
    city = models.CharField(_("City"), max_length=255)
    address = models.CharField(_("Address"), max_length=255)
    postal_code = models.CharField(_("Postal code"), max_length=20)
    file = models.FileField(_("File"), upload_to=get_addr_doc_upload_path)
    status = models.CharField(
        _("Status"),
        choices=VerificationStatus.choices,
        default=VerificationStatus.NO_DATA,
    )


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
