from django.db.models import CharField, TextField, ImageField, URLField, Model

from core.utils import blank_and_null


class Answer(Model):
    title = CharField(max_length=255)
    text = TextField()
    image = ImageField(upload_to="faq/answer/", **blank_and_null)
    video = URLField(blank=True)

    class Meta:
        verbose_name = "Вопрос-ответ"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title
