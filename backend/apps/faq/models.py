from django.db.models import Model

from core.localized.fields import (
    LocalizedCharField,
    LocalizedTextField,
    LocalizedFileField,
    LocalizedURLField,
)
from core.utils import blank_and_null


class Answer(Model):
    title = LocalizedCharField(max_length=255)
    text = LocalizedTextField()
    image = LocalizedFileField(upload_to="faq/answer/", **blank_and_null)
    video = LocalizedURLField(blank=True)

    class Meta:
        verbose_name = "Вопрос-ответ"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title.translate()
