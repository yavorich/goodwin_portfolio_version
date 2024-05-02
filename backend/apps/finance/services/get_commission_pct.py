from apps.finance.models.wallet import WalletSettings


def get_commission_pct(wallet, attr):
    personal_settings = WalletSettings.objects.get(wallet=wallet)
    base_settings = WalletSettings.objects.get(wallet__isnull=True)
    comm_pct = getattr(personal_settings, attr) or getattr(base_settings, attr)
    return comm_pct
