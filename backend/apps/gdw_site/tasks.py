from celery import shared_task
from asgiref.sync import async_to_sync, sync_to_async
from config.settings import (
    NEWS_BOT,
    TELEGRAM_NEWS_CHANNELS,
    TELEGRAM_PHONE_NUMBER,
)
from apps.gdw_site.services.news import sync_message
from apps.gdw_site.models.news import NEWS_MODELS


@shared_task
def sync_all_telegram_news():
    async_to_sync(sync_all_telegram_news_async)()


async def sync_all_telegram_news_async():
    await NEWS_BOT.start(phone=TELEGRAM_PHONE_NUMBER)
    for lang in TELEGRAM_NEWS_CHANNELS:
        channel = await NEWS_BOT.get_entity(TELEGRAM_NEWS_CHANNELS[lang])

        async for message in NEWS_BOT.iter_messages(channel, limit=None):
            with open("log.txt", "a") as f:
                f.write(f"{lang} {message.id}\n")
            await sync_message(message)

        model = NEWS_MODELS[lang]
        deleted_news = await sync_to_async(model.objects.filter)(
            is_sync=False, sync_with_tg=True
        )
        await deleted_news.aupdate(sync_with_tg=False, message_id=None)


@shared_task
def find_and_sync_message(message_id: int, lang: str):
    async_to_sync(find_and_sync_message_async)(message_id, lang)


async def find_and_sync_message_async(message_id: int, lang: str):
    channel = await NEWS_BOT.get_entity(TELEGRAM_NEWS_CHANNELS[lang])
    async for message in NEWS_BOT.iter_messages(
        channel, limit=None, min_id=message_id - 1, max_id=message_id + 1
    ):
        await sync_message(message)
