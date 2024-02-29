from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.forms import ModelForm

from . import models
from .models import VerificationStatus


@admin.register(models.Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name"]


class SettingsInline(admin.StackedInline):
    model = models.Settings


class PersonalVerificationForm(ModelForm):
    def clean(self):
        super().clean()
        if (
            self.cleaned_data.get("reject_message") == ""
            and self.cleaned_data.get("status") == VerificationStatus.REJECTED
        ):
            self.add_error(
                "reject_message",
                f"При постановке статуса "
                f"{VerificationStatus.REJECTED.label} это поле обязательно",
            )

        if (
            self.cleaned_data.get("status") != VerificationStatus.APPROVED
            and self.cleaned_data.get("file") is None
        ):
            self.add_error(
                "file",
                f"При постановке любого статуса кроме "
                f"{VerificationStatus.APPROVED.label} это поле обязательно",
            )


class PersonalVerificationInline(admin.StackedInline):
    model = models.PersonalVerification
    form = PersonalVerificationForm


class AddressVerificationForm(ModelForm):
    def clean(self):
        super().clean()
        if (
            self.cleaned_data.get("reject_message") == ""
            and self.cleaned_data.get("status") == VerificationStatus.REJECTED
        ):
            self.add_error(
                "reject_message",
                f"При постановке статуса "
                f"{VerificationStatus.REJECTED.label} это поле обязательно",
            )

        if (
            self.cleaned_data.get("status") != VerificationStatus.APPROVED
            and self.cleaned_data.get("file") is None
        ):
            self.add_error(
                "file",
                f"При постановке любого статуса кроме"
                f"{VerificationStatus.APPROVED.label} это поле обязательно",
            )


class AddressVerificationInline(admin.StackedInline):
    model = models.AddressVerification
    form = AddressVerificationForm


class PartnerInline(admin.StackedInline):
    model = models.Partner
    fields = ["partner_id", "region"]


class UserForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = get_user_model()


@admin.register(models.User)
class UserAdmin(UserAdmin):
    form = UserForm
    inlines = [
        SettingsInline,
        PersonalVerificationInline,
        AddressVerificationInline,
        PartnerInline,
    ]

    list_filter = ["is_active", "is_staff", "partner"]
    search_fields = [
        "email",
        "first_name",
        "last_name",
    ]
    ordering = ["-date_joined"]

    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("email", "password")}),)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Личная информация", {"fields": ("first_name", "last_name", "partner")}),
        ("Разрешения", {"fields": ("is_active", "is_staff", "is_superuser")}),
        (
            "Важные даты",
            {"fields": ("last_login", "date_joined", "agreement_date")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        # Убедитесь, что не упоминается поле 'username'
        self.exclude = ("username",)
        return super().get_form(request, obj, **kwargs)


@admin.register(models.Docs)
class DocsAdmin(admin.ModelAdmin):
    list_display = ["document_type", "file"]
