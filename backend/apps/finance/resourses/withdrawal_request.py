from django.db.models import Sum, F
from import_export.resources import ModelResource
from import_export.widgets import DecimalWidget, BooleanWidget

from apps.finance.models import WithdrawalRequest
from core.import_export.fields import ReadOnlyField


class WithdrawalRequestResource(ModelResource):
    done = ReadOnlyField(
        attribute="done", column_name="Выполнено", widget=BooleanWidget()
    )
    created_at = ReadOnlyField(attribute="created_at", column_name="Дата создания")
    done_at = ReadOnlyField(attribute="done_at", column_name="Дата выполнения")
    wallet_id = ReadOnlyField(attribute="wallet_id", column_name="Wallet ID")
    original_amount = ReadOnlyField(
        attribute="original_amount",
        column_name="Списать с кошелька",
        widget=DecimalWidget(),
    )
    amount = ReadOnlyField(
        attribute="amount", column_name="Перевести инвестору", widget=DecimalWidget()
    )
    commission = ReadOnlyField(column_name="Удержать комиссию", widget=DecimalWidget())
    address = ReadOnlyField(attribute="address", column_name="Адрес криптокошелька")
    status = ReadOnlyField(attribute="get_status_display", column_name="Статус")
    reject_message = ReadOnlyField(
        attribute="reject_message", column_name="Причина отказа"
    )

    class Meta:
        model = WithdrawalRequest
        fields = (
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
        )

    @staticmethod
    def dehydrate_commission(obj):
        return obj.original_amount - obj.amount

    def after_export(self, queryset, dataset, **kwargs):
        dataset.title = "withdrawal_request"
        dataset.bottoms = [
            "Итого",
            "",
            "",
            "",
            queryset.aggregate(total=Sum("original_amount"))["total"] or 0,
            queryset.aggregate(total=Sum("amount"))["total"] or 0,
            queryset.annotate(commission=F("original_amount") - F("amount")).aggregate(
                total=Sum("commission")
            )["total"]
            or 0,
            "",
            "",
            "",
        ]
