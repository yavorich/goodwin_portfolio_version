from celery import shared_task
from asgiref.sync import async_to_sync, sync_to_async
from config.settings import NEWS_BOT, TELEGRAM_NEWS_CHANNEL, TELEGRAM_PHONE_NUMBER
from apps.gdw_site.models import SiteNews
from apps.gdw_site.services.news import sync_message


@shared_task
def sync_all_telegram_news():
    async_to_sync(sync_all_telegram_news_async)()


async def sync_all_telegram_news_async():
    await NEWS_BOT.start(phone=TELEGRAM_PHONE_NUMBER)
    channel = await NEWS_BOT.get_entity(TELEGRAM_NEWS_CHANNEL)

    async for message in NEWS_BOT.iter_messages(channel, limit=None):
        await sync_message(message)

    deleted_news = await sync_to_async(SiteNews.objects.filter)(
        is_sync=False, sync_with_tg=True
    )
    await deleted_news.aupdate(sync_with_tg=False, message_id=None)


@shared_task
def find_and_sync_message(message_id: int):
    async_to_sync(find_and_sync_message_async)(message_id)


async def find_and_sync_message_async(message_id: int):
    await NEWS_BOT.start(phone=TELEGRAM_PHONE_NUMBER)
    channel = await NEWS_BOT.get_entity(TELEGRAM_NEWS_CHANNEL)
    async for message in NEWS_BOT.iter_messages(
        channel, limit=None, min_id=message_id - 1, max_id=message_id + 1
    ):
        await sync_message(message)
