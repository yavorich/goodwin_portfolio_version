import os
from django.db import models


def get_upload_path(instance, filename):
    return os.path.join("docs", str(instance.pk), filename)


class Docs(models.Model):
    class Type(models.TextChoices):
        CONTRACT_OFFER = "contract_offer", "Договор оферты"

    document_type = models.CharField(
        "Тип документа",
        choices=Type.choices,
        default=Type.CONTRACT_OFFER,
        primary_key=True,
    )
    file = models.FileField("Файл документа", upload_to=get_upload_path)

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
