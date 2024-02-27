from django.db import models

from core.localized.fields import LocalizedFileField


def get_upload_path(instance, filename):
    pass


class Docs(models.Model):
    class Type(models.TextChoices):
        CONTRACT_OFFER = "contract_offer", "Договор оферты"

    document_type = models.CharField(
        "Тип документа",
        choices=Type.choices,
        default=Type.CONTRACT_OFFER,
        primary_key=True,
    )
    file = LocalizedFileField("Файл документа", upload_to="documents")

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
