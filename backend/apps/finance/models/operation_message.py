from django.db.models import Model, CharField

from apps.finance.models.operation_type import MessageType, DATA_INSERTION
from core.localized.fields import LocalizedTextField


class OperationMessage(Model):
    message_type = CharField(
        "Тип сообщения", max_length=40, choices=MessageType.choices, unique=True
    )
    text = LocalizedTextField("Основной текст")

    class Meta:
        verbose_name = "уведомление"
        verbose_name_plural = "Уведомления в истории операций"

    def __str__(self):
        return self.get_message_type_display()

    @property
    def data_insertions_pretty(self):
        insertions = self._get_insertions()
        header = (
            "Добавьте в текст сообщения в виде: {название}\n\n"
            "Доступные параметры (название: описание)\n\n"
        )
        parameters = "\n".join(
            (f"{slug}: {description}" for slug, description in insertions)
        )
        return header + parameters if len(parameters) > 0 else "-"

    def insertion_iter(self):
        return (slug for slug, description in self._get_insertions())

    def _get_insertions(self):
        data_insertions = DATA_INSERTION.get(self.message_type)
        if data_insertions is None:
            return []

        return data_insertions.items()
