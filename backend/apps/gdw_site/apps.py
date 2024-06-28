from django.apps import AppConfig


class GdwSiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.gdw_site"

    def ready(self) -> None:
        import apps.gdw_site.signals
