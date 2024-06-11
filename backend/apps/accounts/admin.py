from decimal import Decimal
from typing import Any

from django.contrib import admin
from django.db.models import Q, Sum, F
from django.db.models.query import QuerySet
from django.forms import ModelForm, BaseInlineFormSet
from django.http import HttpRequest
from nested_admin.nested import (
    NestedStackedInline,
    NestedTabularInline,
    NestedModelAdmin,
)

from apps.finance.models import (
    Wallet,
    WalletSettings,
    UserProgram,
    Operation,
    WithdrawalRequest,
    UserProgramAccrual,
    OperationHistory,
)
from config.settings import LOGIN_AS_USER_TOKEN
from core.import_export.admin import NoConfirmExportMixin
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
from .resources import UserResource


class TotalStatisticFormSet(BaseInlineFormSet):
    def get_queryset(self):
        queryset = super().get_queryset()
        return list(queryset) + [self.model(**self.get_total_model_kwargs(queryset))]

    @staticmethod
    def get_total_model_kwargs(queryset):
        return {}


class TotalStatisticInlineMixin:
    empty_str = ""
    total_str = "Итого"

    def has_change_permission(self, request, obj=None):
        return False

    @staticmethod
    def is_total_obj(obj):
        return obj.pk is None


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

    @admin.display(description="Средний чек")
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


class SettingsInline(NestedStackedInline):
    model = models.Settings
    # classes = ["collapse"]


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


class PersonalVerificationInline(NestedStackedInline):
    model = PersonalVerification
    form = PersonalVerificationForm
    classes = ["collapse"]


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


class AddressVerificationInline(NestedStackedInline):
    model = AddressVerification
    form = AddressVerificationForm
    classes = ["collapse"]


class PartnerInline(NestedStackedInline):
    model = models.Partner
    fields = ["partner_id", "region"]
    classes = ["collapse"]


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


class UserProgramFormSet(TotalStatisticFormSet):
    @staticmethod
    def get_total_model_kwargs(queryset):
        return {
            "name": "Итого",
            "deposit": queryset.aggregate(total=Sum("deposit"))["total"] or 0,
            "start_date": "",
            "end_date": "",
            "close_date": "",
        }


class UserProgramsInline(TotalStatisticInlineMixin, NestedTabularInline):
    model = UserProgram
    formset = UserProgramFormSet
    can_delete = False
    # classes = ["collapse"]
    max_num = 0
    sortable_field_name = "wallet"

    def get_all_accruals(self):
        return NotImplementedError

    def total_accruals(self, obj: UserProgram):
        if self.is_total_obj(obj):
            query = self.get_all_accruals()
        else:
            query = obj.accruals

        return query.aggregate(total=Sum("amount"))["total"] or 0

    total_accruals.short_description = "Чистая прибыль (после удержания комиссий)"

    def total_accruals_percent(self, obj: UserProgram):
        if self.is_total_obj(obj):
            return self.empty_str

        total = obj.accruals.aggregate(total=Sum("amount"))["total"] or 0
        percent = round(safe_zero_div(total * 100, obj.deposit), 2)
        return f"{percent}%"

    total_accruals_percent.short_description = (
        "Чистая прибыль (после удержания комиссий), %"
    )

    def total_success_fee(self, obj: UserProgram):
        if self.is_total_obj(obj):
            query = self.get_all_accruals()
        else:
            query = obj.accruals

        return query.aggregate(total=Sum("success_fee"))["total"] or 0

    total_success_fee.short_description = "Success fee"

    def total_management_fee(self, obj: UserProgram):
        if self.is_total_obj(obj):
            query = self.get_all_accruals()
        else:
            query = obj.accruals

        return query.aggregate(total=Sum("management_fee"))["total"] or 0

    total_management_fee.short_description = "Management fee"


class ActiveProgramsInline(UserProgramsInline):
    verbose_name_plural = "Активные программы"
    fields = [
        "name",
        "start_date",
        "end_date",
        "deposit",
        "total_accruals",
        "total_accruals_percent",
        "total_success_fee",
        "total_management_fee",
    ]
    readonly_fields = fields

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).filter(status=UserProgram.Status.RUNNING)

    def get_all_accruals(self):
        return UserProgramAccrual.objects.filter(
            program__status=UserProgram.Status.RUNNING,
            program__wallet=self.user.wallet,
        )


class ClosedProgramsInline(UserProgramsInline):
    verbose_name_plural = "Закрытые программы"
    fields = [
        "name",
        "start_date",
        "close_date",
        "deposit",
        "total_accruals",
        "total_accruals_percent",
        "total_success_fee",
        "total_management_fee",
    ]
    readonly_fields = fields

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).filter(status=UserProgram.Status.FINISHED)

    def get_all_accruals(self):
        return UserProgramAccrual.objects.filter(
            program__status=UserProgram.Status.FINISHED,
            program__wallet=self.user.wallet,
        )


class ReplenishmentFormSet(TotalStatisticFormSet):
    @staticmethod
    def get_total_model_kwargs(queryset):
        return {"type": Operation.Type.REPLENISHMENT}


class ReplenishmentInline(TotalStatisticInlineMixin, NestedTabularInline):
    verbose_name_plural = "Пополнения"
    model = Operation
    formset = ReplenishmentFormSet
    fields = ["get_date", "get_amount", "get_commission", "get_amount_net"]
    readonly_fields = fields
    can_delete = False
    # classes = ["collapse"]
    max_num = 0
    fk_name = "wallet"
    sortable_field_name = "wallet"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)
        return qs.filter(type=Operation.Type.REPLENISHMENT, done=True)

    def get_all_objects(self):
        return Operation.objects.filter(
            type=Operation.Type.REPLENISHMENT, done=True, wallet=self.user.wallet
        )

    def get_date(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.total_str

        done_at = getattr(obj, "done_at", None)
        if done_at is None:
            done_at = obj.created_at
        return done_at.strftime("%d.%m.%Y")

    get_date.short_description = "Дата"

    def get_amount(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.get_total_field("amount")
        return obj.amount

    get_amount.short_description = "Сумма перевода"

    def get_commission(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.get_total_field("commission")
        return obj.commission

    get_commission.short_description = "Удержанная комиссия"

    def get_amount_net(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.get_total_field("amount_net")
        return obj.amount_net

    get_amount_net.short_description = "Зачислено в кошелек"

    def get_total_field(self, field):
        return self.get_all_objects().aggregate(total=Sum(field))["total"] or 0


class WithdrawalInline(TotalStatisticInlineMixin, NestedTabularInline):
    verbose_name_plural = "Снятия"
    model = WithdrawalRequest
    formset = TotalStatisticFormSet
    fields = [
        "get_date",
        "get_amount",
        "get_commission",
        "get_amount_net",
        "get_address",
    ]
    readonly_fields = fields
    can_delete = False
    # classes = ["collapse"]
    max_num = 0
    fk_name = "wallet"
    sortable_field_name = "wallet"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)
        return qs.filter(status=WithdrawalRequest.Status.APPROVED)

    def get_all_objects(self):
        return WithdrawalRequest.objects.filter(
            wallet=self.user.wallet, status=WithdrawalRequest.Status.APPROVED
        )

    def get_date(self, obj: WithdrawalRequest):
        if self.is_total_obj(obj):
            return self.total_str

        done_at = getattr(obj, "done_at", None)
        if done_at is None:
            done_at = obj.created_at
        return done_at.strftime("%d.%m.%Y")

    get_date.short_description = "Дата"

    def get_amount(self, obj: WithdrawalRequest):
        if self.is_total_obj(obj):
            return (
                self.get_all_objects().aggregate(total=Sum("original_amount"))["total"]
                or 0
            )

        try:
            return obj.original_amount
        except TypeError:
            return 0

    get_amount.short_description = "Списано с кошелька GDW"

    def get_commission(self, obj: WithdrawalRequest):
        if self.is_total_obj(obj):
            return (
                self.get_all_objects()
                .annotate(commission=F("original_amount") - F("amount"))
                .aggregate(total=Sum("commission"))["total"]
                or 0
            )

        try:
            return obj.original_amount - obj.amount
        except TypeError:
            return 0

    get_commission.short_description = "Удержанная комиссия"

    def get_amount_net(self, obj: WithdrawalRequest):
        if self.is_total_obj(obj):
            return self.get_all_objects().aggregate(total=Sum("amount"))["total"] or 0

        try:
            return obj.amount
        except TypeError:
            return 0

    get_amount_net.short_description = "Отправлено"

    def get_address(self, obj: WithdrawalRequest):
        return obj.address

    get_address.short_description = "Адрес криптокошелька USDT"


class TransferFormSet(TotalStatisticFormSet):
    @staticmethod
    def get_total_model_kwargs(queryset):
        return {"type": Operation.Type.TRANSFER}


class TransfersOutInline(TotalStatisticInlineMixin, NestedTabularInline):
    verbose_name_plural = "Исходящие переводы"
    model = Operation
    formset = TransferFormSet
    fields = [
        "get_done_at",
        "get_id",
        "get_fio",
        "get_amount",
        "get_commission",
        "get_amount_net",
    ]
    readonly_fields = fields
    can_delete = False
    # classes = ["collapse"]
    max_num = 0
    fk_name = "wallet"
    sortable_field_name = "wallet"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)
        return qs.filter(type=Operation.Type.TRANSFER, done=True)

    def get_all_objects(self):
        return Operation.objects.filter(
            type=Operation.Type.TRANSFER, done=True, wallet=self.user.wallet
        )

    def get_total_amount(self):
        return (
            self.get_all_objects()
            .annotate(amount_total=F("amount_free") + F("amount_frozen"))
            .aggregate(total=Sum("amount_total"))["total"]
            or 0
        )

    def get_done_at(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.total_str

        done_at = getattr(obj, "done_at", None)
        if done_at is None:
            done_at = obj.created_at
        return done_at.strftime("%d.%m.%Y %H:%M")

    get_done_at.short_description = "Дата и время перевода"

    def get_id(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.empty_str

        return obj.receiver.user.id

    get_id.short_description = "ID получателя"

    def get_fio(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.empty_str

        return obj.receiver.user.full_name

    get_fio.short_description = "ФИО получателя"

    def get_amount(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.get_total_amount()

        try:
            return obj.amount_free + obj.amount_frozen
        except TypeError:
            return 0

    get_amount.short_description = "Списано с кошелька"

    def get_commission(self, obj: Operation):
        if obj.commission is not None:
            return obj.commission
        try:
            return round(self.get_amount(obj) * Decimal("0.005"), 2)
        except TypeError:
            return 0

    get_commission.short_description = "Удержанная комиссия"

    def get_amount_net(self, obj: Operation):
        if obj.amount_net is not None:
            return obj.amount_net
        try:
            return round(self.get_amount(obj) * Decimal("0.995"), 2)
        except TypeError:
            return 0

    get_amount_net.short_description = "Переведено инвестору"


class TransfersIncInline(TotalStatisticInlineMixin, NestedTabularInline):
    verbose_name_plural = "Входящие переводы"
    model = Operation
    formset = TransferFormSet
    fields = [
        "get_done_at",
        "get_id",
        "get_fio",
        "get_amount_net",
    ]
    readonly_fields = fields
    can_delete = False
    # classes = ["collapse"]
    max_num = 0
    fk_name = "receiver"
    sortable_field_name = "receiver"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)
        return qs.filter(type=Operation.Type.TRANSFER, done=True)

    def get_all_objects(self):
        return Operation.objects.filter(
            type=Operation.Type.TRANSFER, done=True, receiver=self.user.wallet
        )

    def get_total_amount(self):
        return (
            self.get_all_objects()
            .annotate(amount_total=F("amount_free") + F("amount_frozen"))
            .aggregate(total=Sum("amount_total"))["total"]
            or 0
        )

    def get_amount(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.get_total_amount()

        try:
            return obj.amount_free + obj.amount_frozen
        except TypeError:
            return 0

    def get_done_at(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.total_str

        done_at = getattr(obj, "done_at", None)
        if done_at is None:
            done_at = obj.created_at
        return done_at.strftime("%d.%m.%Y %H:%M")

    get_done_at.short_description = "Дата и время перевода"

    def get_id(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.empty_str

        return obj.wallet.user.id

    get_id.short_description = "ID отправителя"

    def get_fio(self, obj: Operation):
        if self.is_total_obj(obj):
            return self.empty_str

        return obj.wallet.user.full_name

    get_fio.short_description = "ФИО отправителя"

    def get_amount_net(self, obj: Operation):
        try:
            return round(self.get_amount(obj) * Decimal("0.995"), 2)
        except TypeError:
            return 0

    get_amount_net.short_description = "Получено"


class WalletSettingsInline(NestedStackedInline):
    verbose_name_plural = "Персональные настройки"
    model = WalletSettings
    fields = [
        "defrost_days",
        "commission_on_replenish",
        "commission_on_withdraw",
        "commission_on_transfer",
        "success_fee",
        "management_fee",
        "extra_fee",
    ]
    can_delete = False
    max_num = 0


class WalletInline(NestedTabularInline):
    verbose_name_plural = "Кошелёк"
    model = Wallet
    fields = ["free", "frozen"]
    readonly_fields = ["frozen"]
    can_delete = False
    # classes = ["collapse"]
    max_num = 0
    inlines = [
        ActiveProgramsInline,
        ClosedProgramsInline,
        ReplenishmentInline,
        WithdrawalInline,
        TransfersOutInline,
        TransfersIncInline,
        WalletSettingsInline,
    ]

    def get_inlines(self, request, obj):
        inlines = super().get_inlines(request, obj)
        for inline in inlines:
            inline.user = obj

        return inlines


@admin.register(models.User)
class UserAdmin(NoConfirmExportMixin, NestedModelAdmin):
    class Media:
        css = {"all": ("remove_inline_subtitles.css",)}  # Include extra css

    change_form_template = "custom_user_change_form.html"
    resource_classes = [UserResource]
    list_display = [
        "id",
        "region",
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
    list_display_links = ("id", "region", "fio", "email")
    readonly_fields = list_display
    inlines = [
        SettingsInline,
        PersonalVerificationInline,
        AddressVerificationInline,
        PartnerInline,
        WalletInline,
    ]

    list_filter = [StatusFilter]
    search_fields = ["id", "email", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "id",
                    "email",
                    "fio",
                    "date_joined",
                    "status",
                    "funds_total",
                    "partner",
                )
            },
        ),
    )

    def __init__(self, model: type, admin_site: admin.AdminSite | None) -> None:
        super().__init__(model, admin_site)
        self.opts.verbose_name_plural = "Клиенты"
        self.opts.verbose_name = "клиента"

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def get_form(self, request, obj=None, **kwargs):
        # Убедитесь, что не упоминается поле 'username'
        self.exclude = ("username",)
        return super().get_form(request, obj, **kwargs)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["admin_token"] = LOGIN_AS_USER_TOKEN
        return super(UserAdmin, self).change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).filter(is_active=True, is_staff=False)

    @admin.display(description="ФИО")
    def fio(self, obj: User):
        return obj.full_name

    @admin.display(description="Регион")
    def region(self, obj: User):
        user_region = getattr(obj.partner, "region", None)
        if not user_region:
            partner_profile = getattr(obj, "partner_profile", None)
            user_region = getattr(partner_profile, "region", None)
        return user_region

    @admin.display(description="Статус")
    def status(self, obj: User):
        if Partner.objects.filter(user=obj).exists():
            return "Филиал"
        if obj.verified():
            if obj.wallet.balance > 0:
                return "Инвестор"
            return "Верифицирован"
        if obj.waiting_for_verification():
            return "Ожидает верификации"
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
                total=Sum("deposit")
            )["total"]
            or 0
        )


@admin.register(models.Docs)
class DocsAdmin(admin.ModelAdmin):
    list_display = ["document_type", "file"]


@admin.register(models.Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["name"]


@admin.register(models.ErrorMessage)
class ErrorMessageAdmin(admin.ModelAdmin):
    fields = ("error_type", "data_insertions_pretty", "text")
    readonly_fields = ("error_type", "data_insertions_pretty")
    list_display = ("error_type",)
    list_display_links = ("error_type",)

    @admin.display(description="Параметры для вставки")
    def data_insertions_pretty(self, obj):
        return obj.data_insertions_pretty

    def has_add_permission(self, request, *args, **kwargs):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    fields = ("message_type", "data_insertions_pretty", "title", "text")
    readonly_fields = ("message_type", "data_insertions_pretty")
    list_display = ("message_type",)
    list_display_links = ("message_type",)

    @admin.display(description="Параметры для вставки")
    def data_insertions_pretty(self, obj):
        return obj.data_insertions_pretty

    def has_add_permission(self, request, *args, **kwargs):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class BusinessWalletCommissionsInline(NestedTabularInline):
    verbose_name_plural = "Начисления"
    model = OperationHistory
    fields = ["created_at", "get_operation_type", "amount"]
    readonly_fields = fields
    max_num = 0
    can_delete = False

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).filter(is_commission=True)

    def get_operation_type(self, obj: OperationHistory):
        return Operation.Type(obj.operation_type).label

    get_operation_type.short_description = "Тип комиссии"


class BusinessWalletWithdrawalsInline(NestedTabularInline):
    verbose_name_plural = "Снятия"
    model = OperationHistory
    fields = ["created_at", "amount"]
    readonly_fields = fields
    max_num = 0
    can_delete = False

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return (
            super()
            .get_queryset(request)
            .filter(operation_type=Operation.Type.WITHDRAWAL)
        )


class BusinessWalletInline(NestedTabularInline):
    inlines = [BusinessWalletCommissionsInline, BusinessWalletWithdrawalsInline]
    verbose_name_plural = "Кошелёк"
    model = Wallet
    fields = ["total_income", "free"]
    readonly_fields = ["total_income", "free"]
    can_delete = False
    max_num = 0

    def total_income(self, obj: Wallet):
        return (
            obj.operations_history.filter(is_commission=True).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    total_income.short_description = "Суммарный доход"


@admin.register(models.BusinessAccount)
class BusinessAccountAdmin(NestedModelAdmin):
    class Media:
        css = {"all": ("remove_inline_subtitles.css",)}  # Include extra css

    list_display = [
        "email",
        "first_name",
        "last_name",
        "total_income",
        "current_balance",
    ]
    readonly_fields = ["id"]
    inlines = [BusinessWalletInline]

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "id",
                    "email",
                    "first_name",
                    "last_name",
                )
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return models.BusinessAccount.objects.filter(business_account=True)

    @admin.display(description="Суммарный доход")
    def total_income(self, obj: models.BusinessAccount):
        return (
            obj.wallet.operations_history.filter(is_commission=True).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    @admin.display(description="Доступно для вывода")
    def current_balance(self, obj: models.BusinessAccount):
        return obj.wallet.free
