from django_filters import rest_framework as filters

from apps.finance.models import WalletHistory


class WalletHistoryFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="created_at", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = WalletHistory
        fields = ["start_date", "end_date"]
