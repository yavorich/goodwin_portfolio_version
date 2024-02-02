from django.contrib import admin
from . import models


@admin.register(models.Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "free",
        "frozen",
    ]


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
        "operation",
        "until",
    ]
