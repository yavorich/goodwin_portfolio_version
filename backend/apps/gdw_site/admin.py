from django.contrib import admin

from apps.gdw_site.models import SiteProgram, FundProfitStats


class SiteProgramProfitStatsInline(admin.TabularInline):
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
    inlines = [SiteProgramProfitStatsInline]
