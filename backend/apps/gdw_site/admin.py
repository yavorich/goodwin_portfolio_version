from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest
from django_admin_geomap import ModelAdmin as GeoModelAdmin

from apps.gdw_site.models import (
    SiteProgram,
    FundDailyStats,
    FundMonthlyStats,
    SiteAnswer,
    SiteContact,
)


@admin.register(FundDailyStats)
class FundDailyStatsAdmin(admin.ModelAdmin):
    list_display = ["date", "percent"]
    list_editable = ["percent"]


class FundMonthlyStatsAdminForm(ModelForm):
    class Meta:
        model = FundMonthlyStats
        help_texts = {
            "year": "Укажите значение от 2021 до 2030",
            "month": 'Пара значений "Год" и "Месяц" должна быть уникальной',
        }
        exclude = ()

    def clean(self):
        super().clean()
        if self.cleaned_data.get("year") < 2021 or self.cleaned_data.get("year") > 2030:
            self.add_error("year", "Указанный год не входит в интервал от 2021 до 2030")


@admin.register(SiteProgram)
class SiteProgramAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("remove_inline_subtitles.css",)}  # Include extra css

    list_display = ["name", "annual_profit", "description"]
    # inlines = [FundProfitStatsInline]

    fieldsets = (
        (
            "ПАРАМЕТРЫ ДЛЯ САЙТА",
            {
                "fields": [
                    "annual_profit",
                    "description",
                ],
            },
        ),
    )

    def has_delete_permission(self, request: HttpRequest, obj=...) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


@admin.register(FundMonthlyStats)
class FundMonthlyStatsAdmin(admin.ModelAdmin):
    list_display = ["year", "month", "total"]
    ordering = ["year", "month"]
    list_editable = ["total"]
    form = FundMonthlyStatsAdminForm


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
