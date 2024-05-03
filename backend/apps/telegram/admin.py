from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest

from apps.telegram.models import TemplateTelegramMessage, AdminTelegramAccount
from config.settings import TELEGRAM_BOT_NAME


@admin.register(TemplateTelegramMessage)
class TemplateTelegramMessageAdmin(admin.ModelAdmin):
    fields = ("message_type", "data_insertions_pretty", "text")
    readonly_fields = ("message_type", "data_insertions_pretty")
    list_display = ("message_type",)
    list_display_links = ("message_type",)
    # list_filter = ("message_type",)

    @admin.display(description="Параметры для вставки")
    def data_insertions_pretty(self, obj):
        return obj.data_insertions_pretty

    def has_add_permission(self, request, *args, **kwargs):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class AdminTelegramAccountForm(ModelForm):
    class Meta:
        model = AdminTelegramAccount
        fields = ["tag"]


@admin.register(AdminTelegramAccount)
class AdminTelegramAccountAdmin(admin.ModelAdmin):
    form = AdminTelegramAccountForm
    list_display = ["is_active", "tag", "link", "message"]
    readonly_fields = ["link", "message", "is_active"]

    fieldsets = (
        (
            None,
            {"fields": ("tag",)},
        ),
    )

    @admin.display(description="Ссылка на Telegram-бота")
    def link(self, obj: AdminTelegramAccount):
        return f"https://t.me/{TELEGRAM_BOT_NAME}"

    @admin.display(description="Команда для привязки")
    def message(self, obj: AdminTelegramAccount):
        if not self.is_active(obj):
            return f"/admin {obj.token}"
        return None

    @admin.display(description="Привязан", boolean=True)
    def is_active(self, obj: AdminTelegramAccount):
        return obj.telegram_id is not None

    def has_change_permission(self, request: HttpRequest, obj=...) -> bool:
        return False
