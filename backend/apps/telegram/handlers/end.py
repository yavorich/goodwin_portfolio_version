from aiogram import types
from django.contrib.auth import get_user_model


User = get_user_model()


async def unlink_user_with_telegram(message: types.Message):
    telegram_id = message.chat.id or message.from_user.id
    queryset = User.objects.filter(telegram_id=telegram_id)

    if not await queryset.aexists():
        return await message.reply("Уведомления не привязаны")

    await User.objects.filter(telegram_id=telegram_id).aupdate(
        telegram_id=None,
        telegram=None,
    )
    await message.reply(f"Уведомления для телеграмма отвязаны!")
