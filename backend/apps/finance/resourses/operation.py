from django.db.models import Sum, F, Case, When
from import_export.resources import ModelResource
from import_export.widgets import DecimalWidget

from apps.finance.models import WithdrawalRequest
from core.import_export.fields import ReadOnlyField


class OperationResource(ModelResource):
    operation_type = ReadOnlyField(
        attribute="get_type_display", column_name="Тип транзакции"
    )
    created_at = ReadOnlyField(attribute="created_at", column_name="Дата м время")
    wallet_id = ReadOnlyField(attribute="wallet_id", column_name="Wallet ID")
    fio = ReadOnlyField(attribute="wallet__user__full_name", column_name="ФИО")
    amount = ReadOnlyField(column_name="Сумма", widget=DecimalWidget())
    commission = ReadOnlyField(
        attribute="commission", column_name="Комиссия", widget=DecimalWidget()
    )
    amount_net = ReadOnlyField(
        attribute="amount_net",
        column_name="Сумма с учётом комиссии",
        widget=DecimalWidget(),
    )

    class Meta:
        model = WithdrawalRequest
        fields = (
            "operation_type",
            "created_at",
            "wallet_id",
            "fio",
            "amount",
            "commission",
            "amount_net",
        )

    @staticmethod
    def dehydrate_amount(obj):
        if obj.amount is not None:
            return obj.amount
        return obj.amount_free + obj.amount_frozen

    def after_export(self, queryset, dataset, **kwargs):
        dataset.title = "operation"
        dataset.bottoms = [
            "Итого",
            "",
            "",
            "",
            queryset.annotate(
                res_amount=Case(
                    When(
                        amount__isnull=True, then=F("amount_free") + F("amount_frozen")
                    ),
                    default=F("amount"),
                )
            ).aggregate(total=Sum("res_amount"))["total"]
            or 0,
            queryset.aggregate(total=Sum("commission"))["total"] or 0,
            queryset.aggregate(total=Sum("amount_net"))["total"] or 0,
        ]
