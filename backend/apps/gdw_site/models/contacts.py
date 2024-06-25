from django.db.models import Model, CharField, EmailField, FloatField, BooleanField
from django_admin_geomap import GeoItem


class SiteContact(Model, GeoItem):
    _singleton = BooleanField(default=True, editable=False, unique=True)
    address = CharField("Адрес", max_length=255)
    certificate = CharField("Сертификат", max_length=255)
    email = EmailField("Email")
    latitude = FloatField("Широта")  # широта
    longitude = FloatField("Долгота")  # долгота

    @property
    def geomap_longitude(self):
        return str(self.longitude)

    @property
    def geomap_latitude(self):
        return str(self.latitude)

    def __str__(self) -> str:
        return "Контакты"

    class Meta:
        verbose_name = "значения"
        verbose_name_plural = "Контакты"
