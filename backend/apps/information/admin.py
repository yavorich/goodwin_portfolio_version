from django.contrib import admin
from . import models


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
