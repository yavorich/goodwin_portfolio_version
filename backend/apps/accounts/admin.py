from typing import Any
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models.query import QuerySet
from django.forms import ModelForm
from django.db.models import Q, Sum
from django.http import HttpRequest

from core.utils import safe_zero_div

from . import models
from .models import (
    VerificationStatus,
    Region,
    User,
    Partner,
    PersonalVerification,
    AddressVerification,
)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "investors",
        "total_assets",
        "average_bill",
    ]

    @admin.display(description="Кол-во инвесторов")
    def investors(self, obj: Region):
        return User.objects.filter(partner__region=obj).count()

    @admin.display(description="Сумма активов")
    def total_assets(self, obj: Region):
        return (
            User.objects.filter(partner__region=obj).aggregate(
                total=Sum("wallet__programs__deposit")
            )["total"]
            or 0
        )

    def average_bill(self, obj: Region):
        total_assets = User.objects.filter(partner__region=obj).aggregate(
            total=Sum("wallet__programs__deposit")
        )["total"]
        total_investors = User.objects.filter(partner__region=obj).count()
        return round(safe_zero_div(total_assets, total_investors), 2)


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = [
        "region",
        "partner_id",
        "fio",
        "email",
    ]

    @admin.display(description="ФИО")
    def fio(self, obj: Partner):
        return obj.user.full_name

    @admin.display(description="email")
    def email(self, obj: Partner):
        return obj.user.email

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "partner_id":
            partner_ids = self.model.objects.values_list("partner_id", flat=True)
            help_text = f"Занятые ID партнёров: {', '.join(map(str, partner_ids))}"
            field.help_text = help_text
        return field


class SettingsInline(admin.StackedInline):
    model = models.Settings


class PersonalVerificationForm(ModelForm):
    def clean(self):
        super().clean()
        if (
            self.cleaned_data.get("reject_message") == ""
            and self.cleaned_data.get("status") == VerificationStatus.REJECTED
        ):
            self.add_error(
                "reject_message",
                f"При постановке статуса "
                f"{VerificationStatus.REJECTED.label} это поле обязательно",
            )

        if (
            self.cleaned_data.get("status") != VerificationStatus.APPROVED
            and self.cleaned_data.get("file") is None
        ):
            self.add_error(
                "file",
                f"При постановке любого статуса кроме "
                f"{VerificationStatus.APPROVED.label} это поле обязательно",
            )


class PersonalVerificationInline(admin.StackedInline):
    model = PersonalVerification
    form = PersonalVerificationForm


class AddressVerificationForm(ModelForm):
    def clean(self):
        super().clean()
        if (
            self.cleaned_data.get("reject_message") == ""
            and self.cleaned_data.get("status") == VerificationStatus.REJECTED
        ):
            self.add_error(
                "reject_message",
                f"При постановке статуса "
                f"{VerificationStatus.REJECTED.label} это поле обязательно",
            )

        if (
            self.cleaned_data.get("status") != VerificationStatus.APPROVED
            and self.cleaned_data.get("file") is None
        ):
            self.add_error(
                "file",
                f"При постановке любого статуса кроме "
                f"{VerificationStatus.APPROVED.label} это поле обязательно",
            )
        return self.cleaned_data


class AddressVerificationInline(admin.StackedInline):
    model = AddressVerification
    form = AddressVerificationForm


class PartnerInline(admin.StackedInline):
    model = models.Partner
    fields = ["partner_id", "region"]


# class UserForm(UserChangeForm):
#     class Meta(UserChangeForm.Meta):
#         model = get_user_model()


class StatusFilter(admin.SimpleListFilter):
    title = "По наличию средств на балансе"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return (("active", "Активные"),)

    def queryset(self, request, queryset):
        if self.value() == "active":
            return queryset.filter(Q(wallet__free__gt=0) | Q(wallet__frozen__gt=0))


@admin.register(models.User)
class UserAdmin(UserAdmin):
    # form = UserForm
    list_display = [
        "region",
        "id",
        "fio",
        "email",
        "date_joined",
        "status",
        "wallet_sum",
        "funds_st_1",
        "funds_st_2",
        "funds_st_3",
        "funds_total",
    ]
    inlines = [
        SettingsInline,
        PersonalVerificationInline,
        AddressVerificationInline,
        PartnerInline,
    ]

    list_filter = [StatusFilter]
    search_fields = ["email", "fio"]
    ordering = ["-date_joined"]

    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("email", "password")}),)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Личная информация",
            {"fields": ("first_name", "last_name", "avatar", "partner")},
        ),
        ("Разрешения", {"fields": ("is_active", "is_staff", "is_superuser")}),
        (
            "Важные даты",
            {"fields": ("last_login", "date_joined", "agreement_date")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        # Убедитесь, что не упоминается поле 'username'
        self.exclude = ("username",)
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return (
            super()
            .get_queryset(request)
            .filter(is_active=True, is_staff=False, partner_profile__isnull=True)
        )

    @admin.display(description="ФИО")
    def fio(self, obj: User):
        return obj.full_name

    @admin.display(description="Филиал")
    def region(self, obj: User):
        user_region = getattr(obj.partner, "region", None)
        if not user_region:
            partner_profile = getattr(obj, "partner_profile", None)
            user_region = getattr(partner_profile, "region", None)
        return user_region

    @admin.display(description="Статус")
    def status(self, obj: User):
        if obj.verified():
            if obj.wallet.balance > 0:
                return "Инвестор"
            return "Верифицирован"
        return "Не верифицирован"

    @admin.display(description="Сумма в кошельке")
    def wallet_sum(self, obj: User):
        return obj.wallet.balance

    @admin.display(description="Базовый актив ST-1")
    def funds_st_1(self, obj: User):
        return self.funds_st(obj, name="ST-1")

    @admin.display(description="Базовый актив ST-2")
    def funds_st_2(self, obj: User):
        return self.funds_st(obj, name="ST-2")

    @admin.display(description="Базовый актив ST-3")
    def funds_st_3(self, obj: User):
        return self.funds_st(obj, name="ST-3")

    @admin.display(description="Итого активов")
    def funds_total(self, obj: User):
        return self.funds_st_1(obj) + self.funds_st_2(obj) + self.funds_st_3(obj)

    def funds_st(self, obj: User, name="str"):
        return (
            obj.wallet.programs.filter(program__name=name, status="running").aggregate(
                total=Sum("funds")
            )["total"]
            or 0
        )


@admin.register(models.Docs)
class DocsAdmin(admin.ModelAdmin):
    list_display = ["document_type", "file"]
