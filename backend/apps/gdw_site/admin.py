from django.contrib import admin, messages
from django.forms import ModelForm
from django.http import HttpRequest
from django_admin_geomap import ModelAdmin as GeoModelAdmin

from apps.gdw_site.models import (
    SiteProgram,
    FundDailyStats,
    FundMonthlyStats,
    SiteAnswer,
    SiteContact,
    SiteNews,
    NewsTags,
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


class SiteNewsCreationForm(ModelForm):
    class Meta:
        model = SiteNews
        fields = ["show_on_site", "tag", "image", "title", "text"]


class SiteNewsChangeForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["sync_with_tg"] = False


@admin.register(SiteNews)
class NewsAdmin(admin.ModelAdmin):
    list_display = [
        "message_id",
        "title",
        "show_on_site",
        "sync_with_tg",
        "tag",
        "image",
        "text",
    ]
    list_display_links = ["message_id", "title"]
    list_editable = ["show_on_site", "sync_with_tg"]
    list_filter = ["sync_with_tg", "show_on_site"]
    readonly_fields = ()
    change_list_template = "pagination_on_top.html"
    form = SiteNewsChangeForm

    def has_delete_permission(self, request, obj=None):
        # Разрешить удаление только на странице редактирования объекта
        return obj is not None

    def delete_model(self, request, obj: SiteNews):
        if obj.message_id:
            obj.sync_with_tg = False
            obj.show_on_site = False
            obj.save()
            self.message_user(
                request,
                (
                    "Новость деактивирована, но не удалена, "
                    "т.к. привязана к telegram-посту"
                ),
                level=messages.WARNING,
            )
        else:
            obj.delete()

    def get_form(self, request, obj=None, **kwargs):
        fields = ["show_on_site", "tag", "image", "title", "text"]
        if obj:
            kwargs["fields"] = ["sync_with_tg"] + fields
        else:
            kwargs["fields"] = fields
        return super(NewsAdmin, self).get_form(request, obj, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if not getattr(obj, "message_id", None):
                return ("message_id", "sync_with_tg")
            return ("message_id",)
        return ()

    def save_model(self, request, obj: SiteNews, form, change):
        if change:
            obj.edited_by_admin = True
            if not obj.message_id and obj.sync_with_tg:
                self.message_user(
                    request,
                    "Новость не привязана к telegram-посту",
                    level=messages.ERROR,
                )
                obj.sync_with_tg = False
        super().save_model(request, obj, form, change)


class TagNewsInline(admin.TabularInline):
    model = SiteNews
    extra = 0
    fields = ["message_id", "title", "tag", "image", "text"]


@admin.register(NewsTags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ["tag", "news_count"]
    inlines = [TagNewsInline]

    @admin.display(description="Кол-во новостей")
    def news_count(self, obj: NewsTags):
        return obj.news.count()
