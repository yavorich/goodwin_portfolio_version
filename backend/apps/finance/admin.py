from django.contrib import admin
from django.forms import ModelForm, BaseModelFormSet, ValidationError
from django.http import HttpRequest
from . import models
from .models import (
    UserProgramAccrual,
    WalletHistory,
    Holidays,
    OperationHistory,
    WithdrawalRequest,
)
from ..accounts.models.user import Partner


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
    fields = ["result"]
    extra = 0


@admin.register(models.Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = [
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
    ]
    inlines = [ProgramResultInline]


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
        "name",
        "wallet",
        "status",
        "start_date",
        "end_date",
        "deposit",
        "profit",
        "funds",
    ]
    inlines = [UserProgramReplenishmentInline, UserProgramAccrualInline]


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


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "partner_id":
            partner_ids = self.model.objects.values_list("partner_id", flat=True)
            help_text = f"Занятые ID партнёров: {', '.join(map(str, partner_ids))}"
            field.help_text = help_text
        return field


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
        "address",
        "original_amount",
        "amount",
        "status",
        "reject_message",
    ]
    list_editable = ("status", "reject_message")
    readonly_fields = ("address", "original_amount", "amount", "done")
    fieldsets = (
        (
            None,
            {
                "fields": list_display
            },
        ),
    )

    def get_changelist_formset(self, request, **kwargs):
        kwargs["formset"] = WithdrawalRequestFormSet
        return super().get_changelist_formset(request, **kwargs)
