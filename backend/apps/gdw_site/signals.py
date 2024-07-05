from django.dispatch import receiver
from django.db.models.signals import post_save

from apps.gdw_site.models import SiteNews
from apps.gdw_site.tasks import find_and_sync_message


@receiver(post_save, sender=SiteNews)
def sync_site_news(sender, instance: SiteNews, created: bool, **kwargs):
    if instance.edited_by_admin and instance.sync_with_tg:
        if not instance.same("sync_with_tg"):
            find_and_sync_message.delay(instance.message_id)
