import os

from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager

from core.utils import blank_and_null
from .region import Region
from ..utils import check_is_online


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


def get_upload_path(instance, filename):
    return os.path.join("users", str(instance.pk), "avatar", filename)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    avatar = models.ImageField(
        verbose_name="Аватар", upload_to=get_upload_path, **blank_and_null
    )
    # email_is_confirmed = models.BooleanField(
    #     default=False, verbose_name="Электронная почта подтверждена"
    # )
    agreement_date = models.DateTimeField(
        verbose_name="Дата и время принятия лицензионного соглашения", **blank_and_null
    )
    partner = models.ForeignKey(
        "Partner",
        verbose_name="Привязан к партнёру",
        related_name="users",
        on_delete=models.SET_NULL,
        **blank_and_null,
    )
    telegram = models.CharField(
        max_length=127, verbose_name="Телеграм", blank=True, null=True
    )
    telegram_id = models.IntegerField(**blank_and_null, verbose_name="Телеграмм ID")
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def is_online(self):
        return check_is_online(self)

    @property
    def full_name(self):
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"

    def clean(self) -> None:
        if getattr(self, "partner_profile", None) and self.partner:
            raise ValidationError(
                "Пользователя со статусом партнёра нельзя привязать к другому партнёру."
            )

    def verified(self) -> bool:
        personal = getattr(self, "personal_verification", None)
        address = getattr(self, "address_verification", None)
        personal_status = getattr(personal, "status", None)
        address_status = getattr(address, "status", None)
        return personal_status == address_status == VerificationStatus.APPROVED


class Settings(models.Model):
    user = models.OneToOneField(User, related_name="settings", on_delete=models.CASCADE)
    email_request_code_on_auth = models.BooleanField(
        default=True, verbose_name="(email) Запрашивать код при входе в кабинет"
    )
    email_request_code_on_withdrawal = models.BooleanField(
        default=True, verbose_name="(email) Запрашивать код при выводе средств"
    )
    email_request_code_on_transfer = models.BooleanField(
        default=True, verbose_name="(email) Запрашивать код при внутреннем переводе"
    )
    telegram_request_code_on_auth = models.BooleanField(
        default=False, verbose_name="(telegram) Запрашивать код при входе в кабинет"
    )
    telegram_request_code_on_withdrawal = models.BooleanField(
        default=False, verbose_name="(telegram) Запрашивать код при выводе средств"
    )
    telegram_request_code_on_transfer = models.BooleanField(
        default=False, verbose_name="(telegram) Запрашивать код при внутреннем переводе"
    )

    class Meta:
        verbose_name = "Настройки"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.email


def get_id_doc_upload_path(instance, filename):
    return os.path.join("users", "id", str(instance.user.pk), filename)


def get_addr_doc_upload_path(instance, filename):
    return os.path.join("users", "address", str(instance.user.pk), filename)


class VerificationStatus(models.TextChoices):
    NO_DATA = "no_data", "Нет данных"
    CHECK = "check", "Идёт проверка"
    APPROVED = "approved", "Принято"
    REJECTED = "rejected", "Отказано"


class PersonalVerification(models.Model):
    class DocumentType(models.TextChoices):
        PASSPORT = "passport", "Паспорт"
        ID_CARD = "id_card", "ID карта"
        DRIVER_LICENSE = "driver_license", "Водительские права"
        RESIDENCE_PERMIT = "residence_permit", "Вид на жительство"

    class Gender(models.TextChoices):
        MALE = "male", "Мужской"
        FEMALE = "female", "Женский"

    user = models.OneToOneField(
        User, related_name="personal_verification", on_delete=models.CASCADE
    )
    first_name = models.CharField(max_length=255, verbose_name="Имя")
    last_name = models.CharField(max_length=255, verbose_name="Фамилия")
    gender = models.CharField(choices=Gender.choices, verbose_name="Пол")
    date_of_birth = models.DateField(verbose_name="Дата рождения")
    document_type = models.CharField(
        choices=DocumentType.choices, verbose_name="Тип документа"
    )
    document_issue_date = models.DateField(verbose_name="Дата выдачи документа")
    document_issue_region = models.CharField(
        max_length=255, verbose_name="Регион выдачи документа"
    )
    file = models.FileField(
        upload_to=get_id_doc_upload_path,
        verbose_name="Файл",
        **blank_and_null,
    )
    status = models.CharField(
        choices=VerificationStatus.choices,
        verbose_name="Статус проверки",
        default=VerificationStatus.NO_DATA,
    )
    reject_message = models.TextField(blank=True, verbose_name="Причина отказа")

    class Meta:
        verbose_name = "Документ, подтверждающий личность"
        verbose_name_plural = "Документы, подтверждающие личность"

    def __str__(self):
        return (
            f"{self.get_document_type_display()} "
            f"- {self.first_name} {self.last_name}"
        )


class AddressVerification(models.Model):
    class DocumentType(models.TextChoices):
        REGISTRATION = "registration", "Прописка"
        UTILITY_BILL = "utility_bill", "Счёт за коммунальные услуги"
        BANK_STATEMENT = "bank_statement", "Банковская выписка"
        OTHER = "other", "Другое"

    user = models.OneToOneField(
        User, related_name="address_verification", on_delete=models.CASCADE
    )
    country = models.CharField(max_length=255, verbose_name="Страна")
    city = models.CharField(max_length=255, verbose_name="Город")
    address = models.CharField(max_length=255, verbose_name="Адрес")
    postal_code = models.CharField(max_length=20, verbose_name="Почтовый индекс")
    document_type = models.CharField(
        choices=DocumentType.choices,
        default=DocumentType.REGISTRATION,
        verbose_name="Тип документа",
    )
    file = models.FileField(
        upload_to=get_addr_doc_upload_path, verbose_name="Файл", **blank_and_null
    )
    status = models.CharField(
        choices=VerificationStatus.choices,
        default=VerificationStatus.NO_DATA,
        verbose_name="Статус проверки",
    )
    reject_message = models.TextField(verbose_name="Причина отказа", blank=True)

    class Meta:
        verbose_name = "Документ, подтверждающий адрес"
        verbose_name_plural = "Документы, подтверждающие адрес"

    def __str__(self):
        return f"{self.country}, {self.city}, {self.address}"


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


class Partner(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="partner_profile",
        verbose_name="Пользователь-партнёр",
    )
    partner_id = models.IntegerField(
        unique=True,
        validators=[MinValueValidator(0)],
        verbose_name="ID филиала",
    )
    region = models.ForeignKey(
        Region,
        verbose_name="Регион",
        related_name="partners",
        on_delete=models.CASCADE,
    )
    partner_fee = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.27,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Комиссия филиала/партнёра",
    )

    class Meta:
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"

    def __str__(self):
        return f"{self.region} - {self.partner_id} ({self.user})"


class UserCountHistory(models.Model):
    total = models.PositiveIntegerField("Кол-во зарегистрированных пользователей")
    active = models.PositiveIntegerField("Кол-во активных пользователей")
    created_at = models.DateField(auto_now_add=True, unique=True)

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "История пользователей"
