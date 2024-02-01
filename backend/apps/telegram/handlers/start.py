from aiogram import types

from apps.telegram.models import ConfirmationCode
from core.utils import get_sync_attr


async def link_user_with_telegram(message: types.Message):
    code = message.text.replace("/start ", "")

    chat_id = message.chat.id or message.from_user.id
    confirmation_code = await ConfirmationCode.objects.filter(code=code).afirst()
    if confirmation_code is None:
        return await message.reply("Код подтверждения не найден")

    user = await get_sync_attr(confirmation_code, "user")
    user.telegram_id = chat_id
    user.telegram = message.from_user.username
    await user.asave()

    await confirmation_code.adelete()
    await message.reply("Уведомления для телеграмма привязаны!")
