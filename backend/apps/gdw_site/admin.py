from django.contrib import admin
from django.http import HttpRequest
from django_admin_geomap import ModelAdmin as GeoModelAdmin

from apps.gdw_site.models import (
    SiteProgram,
    FundProfitStats,
    FundTotalStats,
    SiteAnswer,
    SiteContact,
)


class FundProfitStatsInline(admin.TabularInline):
    model = FundProfitStats
    fields = ["date", "percent"]
    readonly_fields = ["date"]
    sortable_by = ["date"]
    verbose_name_plural = "Статистика"
    can_delete = False


@admin.register(SiteProgram)
class SiteProgramAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("remove_inline_subtitles.css",)}  # Include extra css

    list_display = ["name", "annual_profit", "description"]
    inlines = [FundProfitStatsInline]


@admin.register(FundTotalStats)
class FundTotalStatsAdmin(admin.ModelAdmin):
    list_display = ["year", "month", "total"]
    ordering = ["year", "month"]
    list_editable = ["total"]
    readonly_fields = ["year", "month"]

    def has_delete_permission(self, request: HttpRequest, obj=...) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


@admin.register(SiteAnswer)
class SiteAnswerAdmin(admin.ModelAdmin):
    pass


class ContactsAdmin(GeoModelAdmin):
    geomap_field_longitude = "id_longitude"
    geomap_field_latitude = "id_latitude"
    geomap_default_latitude = "45.75583"
    geomap_default_longitude = "37.6173"
    geomap_autozoom = "10"
    list_display = ["address", "certificate", "email"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=...) -> bool:
        return False


admin.site.register(SiteContact, ContactsAdmin)
