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
        abstract = True
        verbose_name = "тег"
        ordering = ["tag"]

    def __str__(self) -> str:
        return str(self.tag)


class NewsTagsRus(NewsTags):
    class Meta:
        verbose_name_plural = "Новостные теги (RU)"


class NewsTagsEng(NewsTags):
    class Meta:
        verbose_name_plural = "Новостные теги (EN)"


class SiteNews(Model):
    message_id = PositiveIntegerField("ID поста в Telegram", unique=True, null=True)
    image = ImageField("Изображение", upload_to=get_upload_path, **blank_and_null)
    title = CharField("Заголовок", max_length=128, **blank_and_null)
    text = TextField("Текст", **blank_and_null)
    date = DateField("Дата публикации", **blank_and_null)
    is_sync = BooleanField("Синхронизирован", default=True)
    show_on_site = BooleanField("Показывать на сайте", default=True)
    sync_with_tg = BooleanField("Синхронизировать с Telegram", default=False)
    edited_by_admin = BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ["-date"]
        verbose_name = "новость"

    def same(self, field: str):
        previous = self.tracker.previous
        return previous(field) == getattr(self, field)

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = now().date()
        super().save(*args, **kwargs)


class SiteNewsRus(SiteNews):
    tag = ForeignKey(
        NewsTagsRus,
        verbose_name="Тег",
        related_name="news",
        on_delete=SET_NULL,
        **blank_and_null,
    )
    tracker = FieldTracker()

    class Meta:
        verbose_name_plural = "Новости (RU)"


class SiteNewsEng(SiteNews):
    tag = ForeignKey(
        NewsTagsEng,
        verbose_name="Тег",
        related_name="news",
        on_delete=SET_NULL,
        **blank_and_null,
    )
    tracker = FieldTracker()

    class Meta:
        verbose_name_plural = "Новости (EN)"


NEWS_MODELS = {"ru": SiteNewsRus, "en": SiteNewsEng}
TAGS_MODELS = {"ru": NewsTagsRus, "en": NewsTagsEng}
