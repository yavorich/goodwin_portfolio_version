from apps.finance.models import Program


class SiteProgram(Program):
    class Meta:
        proxy = True
        verbose_name_plural = "Программы на GDW-сайте"
        verbose_name = "Программа"
