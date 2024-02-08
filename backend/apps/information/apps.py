from django.apps import AppConfig


class InformationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.information"

    def ready(self) -> None:
        # flake8: noqa: F401
        import apps.information.signals
