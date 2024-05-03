from aiogram import types
from django.core.exceptions import ValidationError

from apps.telegram.models import AdminTelegramAccount
from apps.telegram.utils import asend_telegram_message


async def link_admin_with_telegram(message: types.Message):
    token = message.text.replace("/admin", "").strip()
    chat_id = message.chat.id or message.from_user.id
    tag = message.from_user.username.lower()

    try:
        account = await AdminTelegramAccount.objects.filter(
            token=token, tag=tag
        ).afirst()
    except ValidationError:
        return await asend_telegram_message(chat_id, "Действие отклонено")
    if account is None:
        return await asend_telegram_message(chat_id, "Действие отклонено")

    account.telegram_id = chat_id
    await account.asave()
    return await asend_telegram_message(
        chat_id, "Административный аккаунт успешно привязан"
    )
