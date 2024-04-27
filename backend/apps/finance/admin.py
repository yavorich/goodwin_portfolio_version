from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.forms import ModelForm, BaseModelFormSet, ValidationError
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpRequest
from django.db.models import Sum
from . import models
from .models import (
    Program,
    UserProgram,
    UserProgramAccrual,
    WalletHistory,
    Holidays,
    OperationHistory,
    WithdrawalRequest,
    Stats,
)


class FrozenItemInline(admin.TabularInline):
    model = models.FrozenItem
    fields = ["amount", "defrost_date"]
    classes = ["collapse"]


@admin.register(models.Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        "user_id",
        "user",
        "free",
        "frozen",
    ]
    inlines = [FrozenItemInline]


@admin.register(WalletHistory)
class WalletHistoryAdmin(admin.ModelAdmin):
    list_display = ["user", "free", "frozen", "deposits"]
    readonly_fields = ("created_at",)


class ProgramResultInline(admin.TabularInline):
    model = models.ProgramResult
    fields = ["created_at", "result"]
    readonly_fields = fields
    can_delete = False
    max_num = 0
    classes = ["collapse"]
    verbose_name_plural = "РЕЗУЛЬТАТЫ"


class UserProgramInline(admin.TabularInline):
    model = models.UserProgram
    classes = ["collapse"]
    max_num = 0
    can_delete = False

    def get_id(self, obj: UserProgram):
        return obj.wallet.user.id

    get_id.short_description = "ID"

    def fio(self, obj: UserProgram):
        return obj.wallet.user.full_name

    fio.short_description = "ФИО"

    def email(self, obj: UserProgram):
        return obj.wallet.user.email

    def total_accruals(self, obj: UserProgram):
        return obj.accruals.aggregate(total=Sum("amount"))["total"]

    def total_success_fee(self, obj: UserProgram):
        return obj.accruals.aggregate(total=Sum("success_fee"))["total"]

    def total_management_fee(self, obj: UserProgram):
        return obj.accruals.aggregate(total=Sum("management_fee"))["total"]


class UserProgramActiveInline(UserProgramInline):
    fields = [
        "get_id",
        "fio",
        "email",
        "deposit",
        "start_date",
        "total_accruals",
        "total_success_fee",
        "total_management_fee",
    ]
    readonly_fields = fields
    verbose_name_plural = "АКТИВНЫЕ ПРОГРАММЫ"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        queryset = super().get_queryset(request)
        return queryset.filter(status=UserProgram.Status.RUNNING)


class UserProgramClosedInline(UserProgramInline):
    fields = [
        "get_id",
        "fio",
        "email",
        "deposit",
        "start_date",
        "close_date",
        "total_accruals",
        "total_success_fee",
        "total_management_fee",
    ]
    readonly_fields = fields
    verbose_name_plural = "ЗАКРЫТЫЕ ПРОГРАММЫ"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        queryset = super().get_queryset(request)
        return queryset.filter(status=UserProgram.Status.FINISHED)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("custom_admin.css",)}  # Include extra css

    list_display = [
        "get_name",
        "count",
        "total_deposit",
        "total_accruals",
        "total_success_fee",
        "total_management_fee",
    ]
    ordering = ["name"]
    inlines = [ProgramResultInline, UserProgramActiveInline, UserProgramClosedInline]
    fieldsets = (
        (
            "ПАРАМЕТРЫ",
            {
                "classes": ("collapse",),
                "fields": [
                    "name",
                    "duration",
                    "exp_profit",
                    "min_deposit",
                    "accrual_type",
                    "withdrawal_type",
                    "max_risk",
                    "success_fee",
                    "management_fee",
                    "withdrawal_terms",
                ],
            },
        ),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=...) -> bool:
        return False

    @admin.display(description="Название")
    def get_name(self, obj: Program):
        return format_html('<h3 style="color: blue">{}</h3>', obj.name)

    @admin.display(description="Количество программ")
    def count(self, obj: Program):
        active = obj.users.filter(status=UserProgram.Status.RUNNING).count()
        closed = obj.users.filter(status=UserProgram.Status.FINISHED).count()
        return format_html(
            '<h3 style="color: blue">Активные: {}</h3><h3><br>Закрытые: {}</h3>',
            active,
            closed,
        )

    @admin.display(description="Базовый актив")
    def total_deposit(self, obj: Program):
        active = obj.users.filter(status=UserProgram.Status.RUNNING).aggregate(
            total=Sum("deposit")
        )["total"]
        closed = obj.users.filter(status=UserProgram.Status.FINISHED).aggregate(
            total=Sum("deposit")
        )["total"]
        return format_html(
            '<h3 style="color: blue">{}</h3><br><h3>{}</h3>', active, closed
        )

    @admin.display(description="Начислено прибыли")
    def total_accruals(self, obj: Program):
        active = UserProgramAccrual.objects.filter(
            program__status=UserProgram.Status.RUNNING, program__program=obj
        ).aggregate(total=Sum("amount"))["total"]
        closed = UserProgramAccrual.objects.filter(
            program__status=UserProgram.Status.FINISHED, program__program=obj
        ).aggregate(total=Sum("amount"))["total"]
        return format_html(
            '<h3 style="color: blue">{}</h3><br><h3>{}</h3>', active, closed
        )

    @admin.display(description="Удержано Success Fee")
    def total_success_fee(self, obj: Program):
        active = UserProgramAccrual.objects.filter(
            program__status=UserProgram.Status.RUNNING, program__program=obj
        ).aggregate(total=Sum("success_fee"))["total"]
        closed = UserProgramAccrual.objects.filter(
            program__status=UserProgram.Status.FINISHED, program__program=obj
        ).aggregate(total=Sum("success_fee"))["total"]
        return format_html(
            '<h3 style="color: blue">{}</h3><br><h3>{}</h3>', active, closed
        )

    @admin.display(description="Удержано Management Fee")
    def total_management_fee(self, obj: Program):
        active = UserProgramAccrual.objects.filter(
            program__status=UserProgram.Status.RUNNING, program__program=obj
        ).aggregate(total=Sum("management_fee"))["total"]
        closed = UserProgramAccrual.objects.filter(
            program__status=UserProgram.Status.FINISHED, program__program=obj
        ).aggregate(total=Sum("management_fee"))["total"]
        return format_html(
            '<h3 style="color: blue">{}</h3><br><h3>{}</h3>', active, closed
        )


@admin.register(models.ProgramResult)
class ProgramResultAdmin(admin.ModelAdmin):
    list_display = [
        "result",
        "created_at",
        "program",
    ]


class UserProgramReplenishmentInline(admin.TabularInline):
    model = models.UserProgramReplenishment
    fields = ["amount", "status", "apply_date", "done"]
    readonly_fields = ("amount", "apply_date", "done")
    can_delete = False
    extra = 0


class UserProgramAccrualInline(admin.TabularInline):
    model = models.UserProgramAccrual
    fields = ["amount", "percent_amount", "success_fee", "management_fee", "created_at"]
    extra = 0

    def has_change_permission(self, request: HttpRequest, obj=...) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=...) -> bool:
        return False

    # def has_add_permission(self, request: HttpRequest, obj=...) -> bool:
    #     return False


@admin.register(models.UserProgram)
class UserProgramAdmin(admin.ModelAdmin):
    list_display = [
        "wallet_id",
        "full_name",
        "get_created_at",
        "get_start_date",
        "get_deposit",
        "program_name",
        "status",
    ]

    list_editable = ["status"]
    inlines = [UserProgramReplenishmentInline, UserProgramAccrualInline]

    def __init__(self, model: type, admin_site: admin.AdminSite | None) -> None:
        super().__init__(model, admin_site)
        self.opts.verbose_name_plural = "Запуск в программы"
        self.opts.verbose_name = "программу пользователя"

    @admin.display(description="ФИО")
    def full_name(self, obj: UserProgram):
        return obj.wallet.user.full_name

    @admin.display(description="Дата списания с кошелька")
    def get_created_at(self, obj: UserProgram):
        return obj.created_at.date()

    @admin.display(description="Дата запуска программы")
    def get_start_date(self, obj: UserProgram):
        return obj.start_date

    @admin.display(description="Сумма перевода")
    def get_deposit(self, obj: UserProgram):
        return obj.deposit

    @admin.display(description="Программа")
    def program_name(self, obj: UserProgram):
        return obj.program.name


# class OperationActionsInline(admin.TabularInline):
#     model = models.Action
#     fields = ["type", "name", "target", "target_name", "amount", "created_at"]
#     readonly_fields = ["created_at"]
#     extra = 0


@admin.register(models.Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "type",
        "wallet",
        "amount",
        "created_at",
    ]
    # inlines = [OperationActionsInline]


@admin.register(models.FrozenItem)
class FrozenItemAdmin(admin.ModelAdmin):
    list_display = [
        "wallet",
        "amount",
        "defrost_date",
    ]


@admin.register(UserProgramAccrual)
class PartnerAccrualAdmin(admin.ModelAdmin):
    list_display = ["program", "amount", "success_fee", "management_fee"]
    readonly_fields = ["created_at"]
    # TODO валидация unique together program и created_at


@admin.register(Holidays)
class HolidaysAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date"]
    list_display_links = ["start_date"]


@admin.register(OperationHistory)
class OperationHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "type",
        "description",
        "wallet",
        "target_name",
        "amount",
        "created_at",
    ]


class WithdrawalRequestFormSet(BaseModelFormSet):
    def clean(self):
        form_set = self.cleaned_data
        for form_data in form_set:
            if (
                form_data["status"] == WithdrawalRequest.Status.REJECTED
                and form_data["reject_message"] == ""
            ):
                raise ValidationError(
                    f"При постановке статуса {WithdrawalRequest.Status.REJECTED.label}"
                    f" необходимо указать причину отказа.",
                )

        return form_set


class WithdrawalRequestForm(ModelForm):
    def clean(self):
        super().clean()
        if (
            self.cleaned_data["status"] == WithdrawalRequest.Status.REJECTED
            and self.cleaned_data["reject_message"] == ""
        ):
            self.add_error(
                "reject_message",
                f"При постановке статуса {WithdrawalRequest.Status.REJECTED.label}"
                f" это поле не должно быть пустым.",
            )

        return self.cleaned_data


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    form = WithdrawalRequestForm
    list_display = [
        "done",
        "created_at",
        "done_at",
        "wallet_id",
        "original_amount",
        "amount",
        "commission",
        "address",
        "status",
        "reject_message",
    ]
    list_editable = ("status", "reject_message")
    readonly_fields = (
        "done",
        "done_at",
        "created_at",
        "address",
        "original_amount",
        "amount",
        "done",
        "wallet_id",
        "commission",
    )
    fieldsets = (
        (
            None,
            {"fields": list_display},
        ),
    )

    def get_changelist_formset(self, request, **kwargs):
        kwargs["formset"] = WithdrawalRequestFormSet
        return super().get_changelist_formset(request, **kwargs)

    @admin.display(description="Удержать комиссию")
    def commission(self, obj: WithdrawalRequest):
        return obj.original_amount - obj.amount


@admin.register(Stats)
class StatsAdmin(admin.ModelAdmin):
    list_display = [
        "get_name",
        "get_today",
        "get_this_month",
        "get_last_month",
        "get_two_months_ago",
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=...) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=...) -> bool:
        return False

    @admin.display(description="Показатель")
    def get_name(self, obj: Stats):
        url = reverse("admin:accounts_user_changelist")
        if obj.name == Stats.Name.USERS_TOTAL:
            return format_html(
                '<div style="margin-top: 30px"><a href="{}">{}</a></div>',
                url,
                Stats.Name(obj.name).label,
            )
        if obj.name == Stats.Name.USERS_ACTIVE:
            return format_html(
                '<a href="{}">{}</a>',
                url + "?status=active",
                Stats.Name(obj.name).label,
            )
        if obj.name == Stats.Name.TOTAL_FUND_BALANCE:
            return format_html(
                '<h3 style="margin-bottom: 30px; padding: 0">{}</h3>',
                Stats.Name(obj.name).label,
            )
        else:
            return Stats.Name(obj.name).label

    @admin.display(description="Сегодня")
    def get_today(self, obj: Stats):
        if obj.name == Stats.Name.USERS_TOTAL:
            return format_html(
                '<div style="margin-top: 30px">{}</div>',
                obj.today,
            )
        if obj.name == Stats.Name.TOTAL_FUND_BALANCE:
            return format_html(
                '<h3 style="margin-bottom: 30px; padding: 0">{}</h3>',
                obj.today,
            )
        return obj.today

    @admin.display(description="За текущий месяц")
    def get_this_month(self, obj: Stats):
        if obj.name == Stats.Name.USERS_TOTAL:
            return format_html(
                '<div style="margin-top: 30px">{}</div>',
                obj.this_month,
            )
        if obj.name == Stats.Name.TOTAL_FUND_BALANCE:
            return format_html(
                '<h3 style="margin-bottom: 30px; padding: 0">{}</h3>',
                obj.this_month,
            )
        return obj.this_month

    @admin.display(description="За прошлый месяц")
    def get_last_month(self, obj: Stats):
        if obj.name == Stats.Name.USERS_TOTAL:
            return format_html(
                '<div style="margin-top: 30px">{}</div>',
                obj.last_month,
            )
        if obj.name == Stats.Name.TOTAL_FUND_BALANCE:
            return format_html(
                '<h3 style="margin-bottom: 30px; padding: 0">{}</h3>',
                obj.last_month,
            )
        return obj.last_month

    @admin.display(description="За позапрошлый месяц")
    def get_two_months_ago(self, obj: Stats):
        if obj.name == Stats.Name.USERS_TOTAL:
            return format_html(
                '<div style="margin-top: 30px">{}</div>',
                obj.two_months_ago,
            )
        if obj.name == Stats.Name.TOTAL_FUND_BALANCE:
            return format_html(
                '<h3 style="margin-bottom: 30px; padding: 0">{}</h3>',
                obj.two_months_ago,
            )
        return obj.two_months_ago
