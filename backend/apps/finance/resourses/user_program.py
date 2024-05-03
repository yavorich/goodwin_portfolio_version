from django.db.models import Sum
from import_export.resources import ModelResource
from import_export.widgets import DecimalWidget

from apps.finance.models import UserProgram
from core.import_export.fields import ReadOnlyField


class UserProgramResource(ModelResource):
    wallet_id = ReadOnlyField(attribute="wallet_id", column_name="Wallet ID")
    full_name = ReadOnlyField(attribute="wallet__user__full_name", column_name="ФИО")
    created_at = ReadOnlyField(
        attribute="created_at__date", column_name="Дата списания с кошелька"
    )
    start_date = ReadOnlyField(
        attribute="start_date", column_name="Дата запуска программы"
    )
    deposit = ReadOnlyField(
        attribute="deposit", column_name="Сумма перевода", widget=DecimalWidget()
    )
    program_name = ReadOnlyField(attribute="program__name", column_name="Программа")
    status = ReadOnlyField(attribute="get_status_display", column_name="Статус")

    class Meta:
        model = UserProgram
        fields = (
            "wallet_id",
            "full_name",
            "created_at",
            "start_date",
            "deposit",
            "program_name",
            "status",
        )

    def after_export(self, queryset, dataset, **kwargs):
        dataset.title = "user_programs"
        dataset.bottoms = [
            "Итого",
            "",
            "",
            "",
            queryset.aggregate(total=Sum("deposit"))["total"] or 0,
            "",
            "",
        ]
