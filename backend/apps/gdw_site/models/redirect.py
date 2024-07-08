from django.db.models import Model, URLField, TextChoices, CharField


class RedirectLinks(Model):
    class Type(TextChoices):
        REGISTER = "register", "Регистрация"
        LOGIN = "login", "Логин"

    link_type = CharField("Действие", choices=Type.choices, unique=True)
    url = URLField()

    def __str__(self) -> str:
        return self.Type(self.link_type).label

    class Meta:
        verbose_name = "ссылка"
        verbose_name_plural = "Ссылки для аутентификации"
