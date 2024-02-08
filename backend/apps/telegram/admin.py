from django.contrib import admin

from apps.telegram.models import TemplateTelegramMessage


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
