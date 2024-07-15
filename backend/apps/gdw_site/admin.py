from django.contrib import admin, messages
from django.forms import ModelForm
from django.http import HttpRequest
from django_admin_geomap import ModelAdmin as GeoModelAdmin

from apps.gdw_site.models import (
    SiteProgram,
    FundDailyStats,
    SiteAnswer,
    SiteContact,
    SiteNewsRus,
    SiteNewsEng,
    NewsTagsRus,
    NewsTagsEng,
    SocialContact,
    RedirectLinks,
)


@admin.register(FundDailyStats)
class FundDailyStatsAdmin(admin.ModelAdmin):
    list_display = ["date", "percent", "total"]
    list_editable = ["percent"]
    date_hierarchy = "date"


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


class SiteNewsChangeForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["sync_with_tg"] = False


class NewsAdmin(admin.ModelAdmin):
    list_display = [
        "message_id",
        "date",
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

    def delete_model(self, request, obj: SiteNewsRus):
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
        fields = ["show_on_site", "date", "tag", "image", "title", "text"]
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

    def save_model(self, request, obj: SiteNewsRus, form, change):
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


admin.site.register(SiteNewsRus, NewsAdmin)
admin.site.register(SiteNewsEng, NewsAdmin)


class RusTagNewsInline(admin.TabularInline):
    model = SiteNewsRus
    extra = 0
    fields = ["message_id", "title", "tag", "image", "text"]


class EngTagNewsInline(admin.TabularInline):
    model = SiteNewsEng
    extra = 0
    fields = ["message_id", "title", "tag", "image", "text"]


class RusTagsAdmin(admin.ModelAdmin):
    list_display = ["tag", "news_count"]
    inlines = [RusTagNewsInline]

    @admin.display(description="Кол-во новостей")
    def news_count(self, obj: NewsTagsRus):
        return obj.news.count()


class EngTagsAdmin(admin.ModelAdmin):
    list_display = ["tag", "news_count"]
    inlines = [EngTagNewsInline]

    @admin.display(description="Кол-во новостей")
    def news_count(self, obj: NewsTagsRus):
        return obj.news.count()


admin.site.register(NewsTagsRus, RusTagsAdmin)
admin.site.register(NewsTagsEng, EngTagsAdmin)

admin.site.register(SocialContact)


@admin.register(RedirectLinks)
class RedirectLinksAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request: HttpRequest, obj=...) -> bool:
        return False
