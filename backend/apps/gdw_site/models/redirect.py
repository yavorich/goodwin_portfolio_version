from django.db.models import Model, TextChoices, CharField

from core.localized.fields import LocalizedURLField


class RedirectLinks(Model):
    class Type(TextChoices):
        REGISTER = "register", "Регистрация"
        LOGIN = "login", "Логин"

    link_type = CharField("Действие", choices=Type.choices, unique=True)
    url = LocalizedURLField()

    def __str__(self) -> str:
        return self.Type(self.link_type).label

    class Meta:
        verbose_name = "ссылка"
        verbose_name_plural = "Ссылки для аутентификации"
