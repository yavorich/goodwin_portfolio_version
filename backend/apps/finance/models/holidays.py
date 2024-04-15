from django.db.models import Model, DateField, CharField

from core.utils import blank_and_null


class Holidays(Model):
    name = CharField(max_length=255, verbose_name="Название", **blank_and_null)
    start_date = DateField(verbose_name="Дата начала")
    end_date = DateField(
        verbose_name="Дата окончания",
        help_text="Не заполняйте для праздника длящегося один день",
        **blank_and_null,
    )

    class Meta:
        verbose_name = "Праздник"
        verbose_name_plural = "Праздники"

    def __str__(self):
        return f"{self.start_date} - {self.end_date or self.start_date}"
