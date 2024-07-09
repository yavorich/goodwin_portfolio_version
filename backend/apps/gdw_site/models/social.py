import os
from django.db.models import Model, FileField

from core.localized.fields import LocalizedCharField


def get_upload_path(instance, filename):
    return os.path.join("social", str(instance.pk), filename)


class SocialContact(Model):
    service = LocalizedCharField("Сервис", max_length=32)
    link = LocalizedCharField("Ссылка", blank=True)
    logo = FileField(upload_to=get_upload_path, null=True)

    def __str__(self) -> str:
        return self.service.ru

    class Meta:
        verbose_name = "соцсеть"
        verbose_name_plural = "Соцсети"
        ordering = ["service"]
