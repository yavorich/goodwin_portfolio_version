from decimal import Decimal
from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.forms import (
    ModelForm,
    BaseModelFormSet,
    ValidationError,
    TextInput,
    Textarea,
)
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpRequest
from django.db.models import Sum, Count, F, CharField, TextField
from django.db.models.functions import Coalesce
from . import models
from .models import (
    Program,
    UserProgram,
    UserProgramAccrual,
    Holidays,
    WithdrawalRequest,
    Stats,
    Operation,
    WalletSettings,
)


class UserProgramInline(admin.TabularInline):
    model = UserProgram
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


class ProgramAdminForm(ModelForm):

    class Meta:
        model = Program
        help_texts = {
            "success_fee": 'Можно изменить во вкладке "Общие настройки"',
            "management_fee": 'Можно изменить во вкладке "Общие настройки"',
        }
        exclude = ()


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("remove_inline_subtitles.css",)}  # Include extra css

    form = ProgramAdminForm
    list_display = [
        "get_name",
        "count",
        "total_deposit",
        "total_accruals",
        "total_success_fee",
        "total_management_fee",
    ]
    readonly_fields = ["success_fee", "management_fee"]
    ordering = ["name"]
    inlines = [
        # ProgramResultInline,
        UserProgramActiveInline,
        UserProgramClosedInline,
    ]
    fieldsets = (
        (
            "ПАРАМЕТРЫ",
            {
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
        return format_html(
            '<h3 style="color: green; font-size: 20px">{}</h3>', obj.name
        )

    @admin.display(description="Количество программ")
    def count(self, obj: Program):
        active = obj.users.filter(status=UserProgram.Status.RUNNING).count()
        closed = obj.users.filter(status=UserProgram.Status.FINISHED).count()
        return format_html(
            '<h3 style="color: green">Активные: {}</h3><h3><br>Закрытые: {}</h3>',
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
            '<h3 style="color: green">{}</h3><br><h3>{}</h3>', active, closed
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
            '<h3 style="color: green">{}</h3><br><h3>{}</h3>', active, closed
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
            '<h3 style="color: green">{}</h3><br><h3>{}</h3>', active, closed
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
            '<h3 style="color: green">{}</h3><br><h3>{}</h3>', active, closed
        )

    def success_fee(self, obj: Program):
        return WalletSettings.objects.get(wallet__isnull=True).success_fee

    def management_fee(self, obj: Program):
        return WalletSettings.objects.get(wallet__isnull=True).management_fee

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name in ["success_fee", "management_fee"]:
            field.help_text = "Можно изменить в общих настройках"
        return field


@admin.register(models.ProgramResult)
class ProgramResultAdmin(admin.ModelAdmin):
    list_display = [
        "result",
        "until",
        "apply_time",
    ]
    list_editable = [
        "result",
        "until",
        "apply_time",
    ]
    fieldsets = (
        (
            None,
            {"fields": list_display},
        ),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> bool:
        return False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display_links = None


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
    change_list_template = "pagination_on_top.html"
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

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> bool:
        return False


class TypeFilter(admin.SimpleListFilter):
    title = "По типу операции"
    parameter_name = "type"

    def lookups(self, request, model_admin):
        return (
            ("withdrawal", "Вывод"),
            ("replenishment", "Пополнение"),
            ("transfer", "Перевод"),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type=self.value())
        return queryset


@admin.register(models.Operation)
class OperationAdmin(admin.ModelAdmin):
    actions = None
    list_display = [
        "get_type",
        "created_at",
        "wallet_id",
        "fio",
        "get_amount",
        "commission",
        "amount_net",
    ]
    readonly_fields = list_display
    date_hierarchy = "created_at"
    list_filter = [TypeFilter]
    search_fields = [
        "wallet__user__first_name",
        "wallet__user__last_name",
        "wallet__user__id",
    ]

    def __init__(self, model: type, admin_site: admin.AdminSite | None) -> None:
        super().__init__(model, admin_site)
        self.opts.verbose_name_plural = "Транзакции (список)"
        self.opts.verbose_name = "транзакции"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return (
            super()
            .get_queryset(request)
            .filter(
                type__in=[
                    Operation.Type.REPLENISHMENT,
                    Operation.Type.WITHDRAWAL,
                    Operation.Type.TRANSFER,
                ],
                done=True,
            )
        )

    @admin.display(description="Тип транзакции")
    def get_type(self, obj: Operation):
        return obj.get_type_display()

    @admin.display(description="Сумма")
    def get_amount(self, obj: Operation):
        if obj.amount is not None:
            return obj.amount
        return obj.amount_free + obj.amount_frozen

    @admin.display(description="ФИО")
    def fio(self, obj: Operation):
        return obj.wallet.user.full_name

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> bool:
        return False


@admin.register(models.OperationSummary)
class OperationSummaryAdmin(admin.ModelAdmin):
    change_list_template = "grouped_operations.html"

    def __init__(self, model: type, admin_site: admin.AdminSite | None) -> None:
        super().__init__(model, admin_site)
        self.opts.verbose_name_plural = "Транзакции (статистика)"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return (
            super()
            .get_queryset(request)
            .filter(
                type__in=[
                    Operation.Type.REPLENISHMENT,
                    Operation.Type.WITHDRAWAL,
                    Operation.Type.TRANSFER,
                ],
                done=True,
            )
        )

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        try:
            qs = response.context_data["cl"].queryset
        except (AttributeError, KeyError):
            return response

        metrics = {
            "total": Count("id"),
            "total_amount": Sum(
                Coalesce(F("amount_free"), Decimal("0.0"))
                + Coalesce(F("amount_frozen"), Decimal("0.0"))
                + Coalesce(F("amount"), Decimal("0.0"))
            ),
            "total_commission": Sum(Coalesce(F("commission"), Decimal("0.0"))),
            "total_amount_net": Sum(Coalesce(F("amount_net"), Decimal("0.0"))),
        }
        response.context_data["summary"] = list(
            qs.values("type").annotate(**metrics).order_by("type")
        )
        for item in response.context_data["summary"]:
            item["type"] = Operation.Type(item["type"]).label

        response.context_data["summary_total"] = dict(qs.aggregate(**metrics))

        return response

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


@admin.register(Holidays)
class HolidaysAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date"]
    list_display_links = ["start_date"]


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
    formfield_overrides = {
        CharField: {"widget": TextInput(attrs={"size": "10"})},
        TextField: {"widget": Textarea(attrs={"rows": 3, "cols": 30})},
    }
    change_list_template = "pagination_on_top.html"

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

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> bool:
        return False


@admin.register(Stats)
class StatsAdmin(admin.ModelAdmin):
    list_display = [
        "get_name",
        "get_today",
        "get_this_month",
        "get_last_month",
        "get_two_months_ago",
    ]

    def __init__(self, model: type, admin_site: admin.AdminSite | None) -> None:
        super().__init__(model, admin_site)
        self.opts.verbose_name_plural = "Общая статистика"

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


@admin.register(models.WalletSettings)
class WalletSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "defrost_days",
        "commission_on_replenish",
        "commission_on_withdraw",
        "commission_on_transfer",
        "success_fee",
        "management_fee",
        "extra_fee",
    ]
    list_display_links = None
    list_editable = list_display

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).filter(wallet__isnull=True)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> bool:
        return False
