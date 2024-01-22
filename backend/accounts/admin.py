from django.contrib import admin

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


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
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
