from django.db.models import Model

from core.localized.fields import LocalizedCharField, LocalizedTextField


class SiteAnswer(Model):
    title = LocalizedCharField(max_length=255)
    text = LocalizedTextField()

    class Meta:
        verbose_name = "Вопрос-ответ для сайта"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title.translate()
