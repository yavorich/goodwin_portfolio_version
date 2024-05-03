from django.db.models import Sum
from import_export.resources import ModelResource

from apps.accounts.models import User
from core.import_export.fields import ReadOnlyField


class UserResource(ModelResource):
    id = ReadOnlyField(attribute="id", column_name="ID")
    region = ReadOnlyField(attribute="region", column_name="Филиал")
    fio = ReadOnlyField(attribute="full_name", column_name="ФИО")
    email = ReadOnlyField(attribute="email", column_name="Электронная почта")
    date_joined = ReadOnlyField(attribute="date_joined", column_name="Дата регистрации")
    status = ReadOnlyField(column_name="Статус")
    wallet_sum = ReadOnlyField(column_name="Сумма в кошельке")
    funds_st_1 = ReadOnlyField(column_name="Базовый актив ST-1")
    funds_st_2 = ReadOnlyField(column_name="Базовый актив ST-2")
    funds_st_3 = ReadOnlyField(column_name="Базовый актив ST-3")
    funds_total = ReadOnlyField(column_name="Итого активов")

    class Meta:
        model = User
        fields = (
            "id",
            "region",
            "fio",
            "email",
            "date_joined",
            "status",
            "wallet_sum",
            "funds_st_1",
            "funds_st_2",
            "funds_st_3",
            "funds_total",
        )

    @staticmethod
    def dehydrate_region(obj):
        user_region = getattr(obj.partner, "region", None)
        if not user_region:
            partner_profile = getattr(obj, "partner_profile", None)
            user_region = getattr(partner_profile, "region", None)
        return user_region

    @staticmethod
    def dehydrate_status(obj):
        if obj.verified():
            if obj.wallet.balance > 0:
                return "Инвестор"
            return "Верифицирован"
        return "Не верифицирован"

    @staticmethod
    def dehydrate_wallet_sum(obj):
        return obj.wallet.balance

    def dehydrate_funds_st_1(self, obj):
        return self.funds_st(obj, name="ST-1")

    def dehydrate_funds_st_2(self, obj):
        return self.funds_st(obj, name="ST-2")

    def dehydrate_funds_st_3(self, obj):
        return self.funds_st(obj, name="ST-3")

    def dehydrate_funds_total(self, obj):
        return (
            self.dehydrate_funds_st_1(obj)
            + self.dehydrate_funds_st_2(obj)
            + self.dehydrate_funds_st_3(obj)
        )

    def funds_st(self, obj, name):
        return (
            obj.wallet.programs.filter(program__name=name, status="running").aggregate(
                total=Sum("funds")
            )["total"]
            or 0
        )

    def after_export(self, queryset, dataset, **kwargs):
        dataset.title = "users"
