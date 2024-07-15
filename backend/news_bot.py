import asyncio
import django
import os
from telethon import events

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from config.settings import (
    TELEGRAM_NEWS_CHANNELS,
    TELEGRAM_PHONE_NUMBER,
    NEWS_BOT,
)
from apps.gdw_site.services.news import sync_message, delete_message


@NEWS_BOT.on(events.NewMessage(chats=list(TELEGRAM_NEWS_CHANNELS.values())))
async def new_message_handler(event):
    print(f"New post {event.id}")
    await sync_message(event)


@NEWS_BOT.on(events.MessageDeleted(chats=list(TELEGRAM_NEWS_CHANNELS.values())))
async def delete_message_handler(event):
    print(f"Post {event.id} was deleted")
    await delete_message(event)


@NEWS_BOT.on(events.MessageEdited(chats=list(TELEGRAM_NEWS_CHANNELS.values())))
async def edit_message_handler(event):
    print(f"Post {event.id} was edited")
    await sync_message(event)


async def main():
    await NEWS_BOT.start(phone=TELEGRAM_PHONE_NUMBER)
    # with open("session.txt", "w") as f:
    #     f.write(NEWS_BOT.session.save())
    await NEWS_BOT.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
