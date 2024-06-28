import asyncio
import django
import os
from asgiref.sync import sync_to_async
from telethon import events

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from config.settings import (
    TELEGRAM_NEWS_CHANNEL,
    TELEGRAM_PHONE_NUMBER,
    NEWS_BOT
)

from apps.gdw_site.models import SiteNews
from apps.gdw_site.services.news import sync_message


@NEWS_BOT.on(events.NewMessage(chats=[TELEGRAM_NEWS_CHANNEL]))
async def new_message_handler(event):
    print(f"New post {event.id}")
    await sync_message(event)


@NEWS_BOT.on(events.MessageDeleted(chats=[TELEGRAM_NEWS_CHANNEL]))
async def delete_message_handler(event):
    print(f"Post {event.id} was deleted")
    try:
        post = await SiteNews.objects.aget(message_id=event.id, sync_with_tg=True)
        await post.adelete()
    except SiteNews.DoesNotExist:
        pass


@NEWS_BOT.on(events.MessageEdited(chats=[TELEGRAM_NEWS_CHANNEL]))
async def edit_message_handler(event):
    print(f"Post {event.id} was edited")
    await sync_message(event)


async def main():
    # NEWS_BOT.parse_mode = "markdown"
    await NEWS_BOT.start(phone=TELEGRAM_PHONE_NUMBER)
    channel = await NEWS_BOT.get_entity(TELEGRAM_NEWS_CHANNEL)

    async for message in NEWS_BOT.iter_messages(channel, limit=None):
        await sync_message(message)

    deleted_news = await sync_to_async(SiteNews.objects.filter)(
        is_sync=False, sync_with_tg=True
    )
    await deleted_news.aupdate(sync_with_tg=False, message_id=None)
    # with open("session.txt", "w") as f:
    #     f.write(client.session.save())
    print("done")
    await NEWS_BOT.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
