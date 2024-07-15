import re
from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from telethon.tl.types import MessageMediaPhoto
from telethon.errors import TimeoutError

from apps.gdw_site.models.news import NEWS_MODELS, TAGS_MODELS
from config.settings import TELEGRAM_NEWS_CHANNELS


def get_message_language(message):
    language = [
        k for k, v in TELEGRAM_NEWS_CHANNELS.items() if v == message.chat.username
    ][0]
    return language


def find_text_patterns(text):
    soup = BeautifulSoup(text, "html.parser")
    title, tag = None, None
    title_pattern = soup.find("strong")
    tag_pattern = re.compile(r"#\w+")

    if title_pattern and len(str(title_pattern)) < 128:
        title = title_pattern.text
        text = text.replace(str(title_pattern), "")

    tag_matches = tag_pattern.findall(text)

    for match in tag_matches:
        if match not in ["#x27"]:
            tag = match
            text = text.replace(match, "")
            break

    return title, text, tag


async def sync_message(message):
    language = get_message_language(message)
    date = message.date
    text = message.text
    image_content = None
    news_model = NEWS_MODELS[language]
    tags_model = TAGS_MODELS[language]

    # Извлечение изображения из сообщения
    if message.media and isinstance(message.media, MessageMediaPhoto):
        try:
            image_bytes = await message.download_media(bytes)
            if image_bytes:
                image_content = ContentFile(image_bytes)
        except TimeoutError:
            print("Timeout while fetching image data from Telegram.")
        except Exception as e:
            print(f"An error occurred while fetching image data: {e}")

    if text:
        title, text, tag = find_text_patterns(text)
        tag_object, _ = (
            await tags_model.objects.aget_or_create(tag=tag) if tag else (None, None)
        )
        defaults = dict(
            title=title,
            text=text,
            tag=tag_object,
            date=date,
            is_sync=True,
        )

        try:
            post = await news_model.objects.aget(message_id=message.id)

            if await sync_to_async(getattr)(post, "sync_with_tg"):
                for key, value in defaults.items():
                    await sync_to_async(setattr)(post, key, value)
            else:
                await sync_to_async(setattr)(post, "is_sync", False)
            await post.asave()

        except news_model.DoesNotExist:
            post = await news_model.objects.acreate(
                message_id=message.id, sync_with_tg=True, show_on_site=True, **defaults
            )
        if image_content:
            await sync_to_async(post.image.delete)()
            await sync_to_async(post.image.save)(f"{message.id}.jpg", image_content)


async def delete_message(message):
    language = get_message_language(message)
    news_model = NEWS_MODELS[language]
    try:
        post = await news_model.objects.aget(message_id=message.id, sync_with_tg=True)
        await post.adelete()
    except news_model.DoesNotExist:
        pass
