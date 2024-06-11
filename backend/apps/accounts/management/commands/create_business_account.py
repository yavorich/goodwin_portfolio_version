from typing import Any
from decimal import Decimal
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.finance.models import WalletSettings


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        commission_account = User.objects.create_user(
            password="password",
            email="business@goodwin.com",
            first_name="Commission",
            last_name="Manager",
            business_account=True,
        )
        WalletSettings.objects.filter(wallet=commission_account.wallet).update(
            commission_on_withdraw=Decimal("0.0"),
            commission_on_replenish=Decimal("0.0"),
            commission_on_transfer=Decimal("0.0"),
        )
