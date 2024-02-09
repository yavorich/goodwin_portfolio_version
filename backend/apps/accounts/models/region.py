from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=31)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
