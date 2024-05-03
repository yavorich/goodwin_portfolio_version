from django.db.models import Sum
from import_export.resources import ModelResource
from import_export.widgets import DecimalWidget

from apps.finance.models import UserProgram
from core.import_export.fields import ReadOnlyField


class UserProgramResource(ModelResource):
    user_id = ReadOnlyField(attribute="wallet__user_id", column_name="User ID")
    full_name = ReadOnlyField(attribute="wallet__user__full_name", column_name="ФИО")
    email = ReadOnlyField(attribute="wallet__user__email", column_name="Email")
    deposit = ReadOnlyField(
        attribute="deposit", column_name="Базовый депозит", widget=DecimalWidget()
    )
    start_date = ReadOnlyField(attribute="start_date", column_name="Дата начала")
    close_date = ReadOnlyField(
        attribute="close_date", column_name="Фактическая дата завершения"
    )
    total_accruals = ReadOnlyField(column_name="Total accruals", widget=DecimalWidget())
    total_success_fee = ReadOnlyField(
        column_name="Total success fee", widget=DecimalWidget()
    )
    total_management_fee = ReadOnlyField(
        column_name="Total management fee", widget=DecimalWidget()
    )

    class Meta:
        model = UserProgram
        fields = (
            "user_id",
            "full_name",
            "email",
            "deposit",
            "start_date",
            "close_date",
            "total_accruals",
            "total_success_fee",
            "total_management_fee",
        )

    @staticmethod
    def dehydrate_total_accruals(obj):
        return obj.accruals.aggregate(total=Sum("amount"))["total"] or 0

    @staticmethod
    def dehydrate_total_success_fee(obj):
        return obj.accruals.aggregate(total=Sum("success_fee"))["total"] or 0

    @staticmethod
    def dehydrate_total_management_fee(obj):
        return obj.accruals.aggregate(total=Sum("management_fee"))["total"] or 0

    def after_export(self, queryset, dataset, **kwargs):
        dataset.title = "user_programs"
        dataset.bottoms = [
            "Итого",
            "",
            "",
            queryset.aggregate(total=Sum("deposit"))["total"] or 0,
            "",
            "",
            queryset.aggregate(total=Sum("accruals__amount"))["total"] or 0,
            queryset.aggregate(total=Sum("accruals__success_fee"))["total"] or 0,
            queryset.aggregate(total=Sum("accruals__management_fee"))["total"] or 0,
        ]
