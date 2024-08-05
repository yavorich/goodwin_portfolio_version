from django.dispatch import receiver
from django.db.models.signals import post_save

from apps.gdw_site.models import SiteNewsRus, SiteNewsEng
from apps.gdw_site.tasks import find_and_sync_message


# Review можно объединить функции
def sync_site_news(instance, lang):
    if instance.edited_by_admin and instance.sync_with_tg:
        if not instance.same("sync_with_tg") and instance.message_id:
            find_and_sync_message.delay(instance.message_id, lang=lang)


@receiver(post_save, sender=SiteNewsRus)
def sync_site_news_rus(sender, instance: SiteNewsRus, created: bool, **kwargs):
    sync_site_news(instance, "ru")


@receiver(post_save, sender=SiteNewsEng)
def sync_site_news_eng(sender, instance: SiteNewsEng, created: bool, **kwargs):
    sync_site_news(instance, "en")
