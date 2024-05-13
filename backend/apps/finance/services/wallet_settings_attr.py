from django.apps import apps


def get_wallet_settings_attr(wallet, attr):
    WalletSettings = apps.get_model(app_label="finance", model_name="WalletSettings")
    personal_settings = WalletSettings.objects.get(wallet=wallet)
    base_settings = WalletSettings.objects.get(wallet__isnull=True)
    value = getattr(personal_settings, attr) or getattr(base_settings, attr)
    return value
