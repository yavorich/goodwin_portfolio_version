from django.db.models import Model

from core.localized.fields import LocalizedCharField


class SocialContact(Model):
    service = LocalizedCharField("Сервис", max_length=32)
    link = LocalizedCharField("Ссылка", blank=True)

    def __str__(self) -> str:
        return self.service.ru

    class Meta:
        verbose_name = "соцсеть"
        verbose_name_plural = "Соцсети"
        ordering = ["service"]
