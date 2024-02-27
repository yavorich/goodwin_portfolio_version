import asyncio

from aiogram.exceptions import AiogramError, TelegramBadRequest

from config.settings import MAIN_BOT


def aiogram_async_to_sync(func):
    """
    Декоратор для асинхронной отправки сообщений в телеграм
    """

    async def main(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except AiogramError:
            pass
        finally:
            if MAIN_BOT:
                await MAIN_BOT.session.close()
                await asyncio.sleep(0.25)  # для успешного закрытия сессии

    def wrapper(*args, **kwargs):
        asyncio.run(main(*args, **kwargs))

    return wrapper


@aiogram_async_to_sync
async def send_telegram_message(telegram_id, text):
    await asend_telegram_message(telegram_id, text)


async def asend_telegram_message(telegram_id, text):
    try:
        if MAIN_BOT:
            await MAIN_BOT.send_message(telegram_id, text)
    except TelegramBadRequest:
        pass
