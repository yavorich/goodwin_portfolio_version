from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=31)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"


class Country(models.Model):
    name = models.CharField("Название", max_length=63, unique=True)
    is_active = models.BooleanField("Доступна для выбора", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "страну"
        verbose_name_plural = "Страны (для верификации)"
