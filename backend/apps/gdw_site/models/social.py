from django.db.models import Model, CharField

from core.localized.fields import LocalizedCharField


class SocialContact(Model):
    service = CharField("Сервис", max_length=15)
    link = LocalizedCharField("Ссылка", blank=True)

    def __str__(self) -> str:
        return self.service

    class Meta:
        verbose_name = "соцсеть"
        verbose_name_plural = "Соцсети"
        ordering = ["service"]
