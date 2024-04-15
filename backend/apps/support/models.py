from django.db.models import Model, CharField

from core.localized.fields import LocalizedCharField


class Support(Model):
    service = CharField("Сервис", max_length=15)
    link = LocalizedCharField("Ссылка", blank=True)

    def __str__(self) -> str:
        return self.service

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"
        ordering = ["service"]
