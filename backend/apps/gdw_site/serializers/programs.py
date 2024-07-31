from rest_framework.serializers import (
    ModelSerializer,
    FloatField,
    SerializerMethodField,
    CharField,
)

from apps.gdw_site.models import SiteProgram
from apps.finance.services.wallet_settings_attr import get_wallet_settings_attr


class SiteProgramSerializer(ModelSerializer):
    description = CharField()
    min_deposit = FloatField()
    success_fee = SerializerMethodField()
    management_fee = SerializerMethodField()
    withdrawal_terms = SerializerMethodField()
    accrual_type = CharField(source="get_accrual_type_display")
    withdrawal_type = CharField(source="get_withdrawal_type_display")

    class Meta:
        model = SiteProgram
        fields = [
            "id",
            "name",
            "annual_profit",
            "description",
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

    def get_success_fee(self, obj: SiteProgram):
        return float(get_wallet_settings_attr(None, "success_fee"))

    def get_management_fee(self, obj: SiteProgram):
        return float(get_wallet_settings_attr(None, "management_fee"))

    def get_withdrawal_terms(self, obj: SiteProgram):
        return int(get_wallet_settings_attr(None, "defrost_days"))
