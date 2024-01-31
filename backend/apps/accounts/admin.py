from django.contrib import admin
from django.forms import ModelForm, CharField

from . import models


@admin.register(models.Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name"]


class SettingsInline(admin.StackedInline):
    model = models.Settings


class PersonalVerificationInline(admin.StackedInline):
    model = models.PersonalVerification


class AddressVerificationInline(admin.StackedInline):
    model = models.AddressVerification


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
        "first_name",
        "last_name",
        "email",
        "region",
        "is_active",
        "is_staff",
    ]
    inlines = [SettingsInline, PersonalVerificationInline, AddressVerificationInline]


@admin.register(models.Docs)
class DocsAdmin(admin.ModelAdmin):
    list_display = ["document_type", "file"]
