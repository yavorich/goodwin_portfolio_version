from uuid import uuid4
from django.db.models import Model, CharField, UUIDField, IntegerField

from core.utils import blank_and_null


class AdminTelegramAccount(Model):
    tag = CharField("Тег", max_length=127)
    token = UUIDField("Токен привязки", default=uuid4)
    telegram_id = IntegerField(**blank_and_null, verbose_name="Телеграм ID")

    class Meta:
        verbose_name = "аккаунт"
        verbose_name_plural = "Telegram-аккаунты для уведомлений"

    def save(self, *args, **kwargs):
        self.tag = self.tag.lower()
        super().save(*args, **kwargs)
