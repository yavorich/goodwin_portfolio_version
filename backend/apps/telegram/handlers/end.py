from aiogram import types
from django.contrib.auth import get_user_model

from apps.telegram.models import MessageType
from apps.telegram.sender import asend_template_telegram_message

User = get_user_model()


async def unlink_user_with_telegram(message: types.Message):
    telegram_id = message.chat.id or message.from_user.id
    queryset = User.objects.filter(telegram_id=telegram_id)

    if not await queryset.aexists():
        return await message.reply("Уведомления не подключены")

    await User.objects.filter(telegram_id=telegram_id).aupdate(
        telegram_id=None,
        telegram=None,
    )
    await asend_template_telegram_message(telegram_id, MessageType.NOTIFY_DISCONNECTED)
