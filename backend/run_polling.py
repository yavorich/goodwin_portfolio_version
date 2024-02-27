import asyncio
import os, django
from aiogram import Dispatcher

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.telegram.routers import telegram_router
from config.settings import MAIN_BOT


async def main():
    if MAIN_BOT:
        dp = Dispatcher()
        dp.include_routers(telegram_router)
        await dp.start_polling(MAIN_BOT)


if __name__ == "__main__":
    asyncio.run(main())
