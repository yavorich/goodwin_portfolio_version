from aiogram import Router
from aiogram.filters import Command

from apps.telegram.handlers import (
    link_user_with_telegram,
    unlink_user_with_telegram,
    link_admin_with_telegram,
)


telegram_router = Router()


telegram_router.message.register(link_user_with_telegram, Command(commands=["start"]))
telegram_router.message.register(unlink_user_with_telegram, Command(commands=["end"]))
telegram_router.message.register(link_admin_with_telegram, Command(commands=["admin"]))
