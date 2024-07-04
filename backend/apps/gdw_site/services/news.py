from asgiref.sync import async_to_sync, sync_to_async
# from django.core.files.base import ContentFile
# from telethon.tl.types import MessageMediaPhoto
# from telethon.errors import TimeoutError

from config.settings import NEWS_BOT, TELEGRAM_NEWS_CHANNEL, TELEGRAM_PHONE_NUMBER
from apps.gdw_site.models import NewsTags, SiteNews


def find_and_sync_message(message_id):
    async_to_sync(find_and_sync_message_async)(message_id)


async def find_and_sync_message_async(message_id):
    await NEWS_BOT.start(phone=TELEGRAM_PHONE_NUMBER)
    channel = await NEWS_BOT.get_entity(TELEGRAM_NEWS_CHANNEL)
    async for message in NEWS_BOT.iter_messages(
        channel, limit=None, min_id=message_id - 1, max_id=message_id + 1
    ):
        await sync_message(message)


async def sync_message(message):
    date = message.date
    text = message.text
    # image_content = None

    # # Извлечение изображения из сообщения
    # if message.media and isinstance(message.media, MessageMediaPhoto):
    #     try:
    #         image_bytes = await message.download_media(bytes)
    #         if image_bytes:
    #             image_content = ContentFile(image_bytes, name=f"{message.id}.jpg")
    #         print("Timeout while fetching image data from Telegram.")
    #     except Exception as e:
    #         print(f"An error occurred while fetching image data: {e}")

    if text:
        title, text, tag = find_text_patterns(text)
        tag_object, _ = (
            await NewsTags.objects.aget_or_create(tag=tag) if tag else (None, None)
        )
        defaults = dict(
            title=title,
            text=text,
            tag=tag_object,
            date=date,
            is_sync=True,
        )
        # if image_content:
        #     defaults['image'] = image_content

        try:
            post = await SiteNews.objects.aget(message_id=message.id)

            if await sync_to_async(getattr)(post, "sync_with_tg"):
                for key, value in defaults.items():
                    await sync_to_async(setattr)(post, key, value)
            else:
                await sync_to_async(setattr)(post, "is_sync", False)
            await post.asave()

        except SiteNews.DoesNotExist:
            await SiteNews.objects.acreate(
                message_id=message.id, sync_with_tg=True, show_on_site=False, **defaults
            )


def find_text_patterns(text):
    splitted_text = text.split("\n")
    title, tag = None, None
    for sample in splitted_text:
        if "#" not in sample and title is None:
            title_sample = sample.replace("**", "").strip()
            if len(title_sample) < 128:
                title = title_sample
                text = text.replace(sample, "").strip()
        if sample.startswith("#") and " " not in sample and tag is None:
            tag = sample
            text = text.replace(sample, "").strip()
    return title, text, tag
