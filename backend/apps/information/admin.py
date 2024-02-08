from django.contrib import admin
from . import models
from ..accounts.models.user import Partner


@admin.register(models.Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "free",
        "frozen",
    ]


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


class UserProgramReplenishmentInline(admin.TabularInline):
    model = models.UserProgramReplenishment
    fields = ["amount", "status", "apply_date"]
    extra = 0


@admin.register(models.UserProgram)
class UserProgramAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "wallet",
        "start_date",
        "end_date",
        "funds",
        "status",
    ]
    inlines = [UserProgramReplenishmentInline]


@admin.register(models.Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = [
        "type",
        "wallet",
        "amount",
        "created_at",
    ]


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
