from django.contrib import admin
from . import models
from .models import UserProgramAccrual, WalletHistory
from ..accounts.models.user import Partner


class FrozenItemInline(admin.TabularInline):
    model = models.FrozenItem
    fields = ["amount", "defrost_date"]
    classes = ["collapse"]


@admin.register(models.Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
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
    fields = ["amount", "status", "apply_date"]
    extra = 0


class UserProgramAccrualInline(admin.TabularInline):
    model = models.UserProgramAccrual
    fields = ["amount", "success_fee"]
    extra = 0


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


class OperationActionsInline(admin.TabularInline):
    model = models.Action
    fields = ["type", "name", "target", "target_name", "amount"]
    extra = 0


@admin.register(models.Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "type",
        "wallet",
        "amount",
        "created_at",
    ]
    inlines = [OperationActionsInline]


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


# admin.site.register(UserProgramAccrual)


@admin.register(UserProgramAccrual)
class PartnerAccrualAdmin(admin.ModelAdmin):
    list_display = ["program", "amount", "success_fee"]
    readonly_fields = ["created_at"]
