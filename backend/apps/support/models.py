import os

from django.db.models import Model, CharField, FileField

from core.localized.fields import LocalizedCharField


def get_upload_path(instance, filename):
    return os.path.join("contacts", instance.service, filename)


class Support(Model):
    service = CharField("Сервис", max_length=15)
    logo = FileField(upload_to=get_upload_path, null=True)
    link = LocalizedCharField("Ссылка", blank=True)

    def __str__(self) -> str:
        return self.service

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"
        ordering = ["service"]
