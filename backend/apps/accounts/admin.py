from django.contrib import admin
from django.forms import ModelForm, CharField

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


class AddressVerificationInline(admin.StackedInline):
    model = models.AddressVerification
    form = AddressVerificationForm


class UserForm(ModelForm):
    set_password = CharField(
        help_text="Поле для установки пароля администратора.",
        label="Установить пароль",
        required=False,
    )

    def save(self, commit=True):
        password = self.cleaned_data.get("set_password", None)
        user = super().save(commit=commit)
        if password:
            user.set_password(password)
            user.save()
        return user


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    form = UserForm
    list_display = [
        "email",
        "first_name",
        "last_name",
        "region",
        "is_active",
        "is_staff",
    ]
    inlines = [SettingsInline, PersonalVerificationInline, AddressVerificationInline]


@admin.register(models.Docs)
class DocsAdmin(admin.ModelAdmin):
    list_display = ["document_type", "file"]
