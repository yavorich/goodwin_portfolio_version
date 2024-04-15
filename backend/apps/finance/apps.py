from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.finance"

    def ready(self) -> None:
        # flake8: noqa: F401
        import apps.finance.signals
