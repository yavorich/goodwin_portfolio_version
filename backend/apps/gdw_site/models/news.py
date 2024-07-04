import os
from django.db.models import (
    Model,
    ImageField,
    TextField,
    PositiveIntegerField,
    BooleanField,
    CharField,
    DateField,
    ForeignKey,
    SET_NULL,
)
from django.utils.timezone import now
from model_utils.tracker import FieldTracker

from core.utils import blank_and_null


def get_upload_path(instance, filename):
    return os.path.join("news", str(instance.pk), filename)


class NewsTags(Model):
    tag = CharField(max_length=63, unique=True)

    class Meta:
        verbose_name_plural = "Новостные теги"


class SiteNews(Model):
    message_id = PositiveIntegerField("ID поста в Telegram", unique=True, null=True)
    image = ImageField("Изображение", upload_to=get_upload_path, **blank_and_null)
    title = CharField("Заголовок", max_length=128, **blank_and_null)
    text = TextField("Текст", **blank_and_null)
    tag = ForeignKey(
        NewsTags,
        verbose_name="Тег",
        related_name="news",
        on_delete=SET_NULL,
        **blank_and_null,
    )
    date = DateField("Дата публикации", **blank_and_null)
    is_sync = BooleanField("Синхронизирован", default=True)
    show_on_site = BooleanField("Показывать на сайте", default=True)
    sync_with_tg = BooleanField("Синхронизировать с Telegram", default=False)
    edited_by_admin = BooleanField(default=False)

    tracker = FieldTracker()

    class Meta:
        ordering = ["-message_id"]
        verbose_name = "новость"
        verbose_name_plural = "Новости"

    def same(self, field: str):
        previous = self.tracker.previous
        return previous(field) == getattr(self, field)

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = now().date()
        super().save(*args, **kwargs)
