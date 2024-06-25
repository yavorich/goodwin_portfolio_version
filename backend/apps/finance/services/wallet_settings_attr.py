from django.apps import apps


def get_wallet_settings_attr(wallet, attr):
    WalletSettings = apps.get_model(app_label="finance", model_name="WalletSettings")
    if wallet is not None:
        personal_settings = WalletSettings.objects.get(wallet=wallet)
        personal_value = getattr(personal_settings, attr)
        if personal_value is not None:
            return personal_value
    base_settings = WalletSettings.objects.get(wallet__isnull=True)
    base_value = getattr(base_settings, attr)
    return base_value
