from django.contrib import admin
from django.http import HttpRequest

from apps.gdw_site.models import SiteProgram, FundProfitStats, FundTotalStats


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
