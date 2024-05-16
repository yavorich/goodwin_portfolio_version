from datetime import date
from decimal import Decimal

from apps.telegram.models import MessageType, TemplateTelegramMessage
from apps.telegram.utils import asend_telegram_message, aiogram_async_to_sync


@aiogram_async_to_sync
async def send_template_telegram_message(
    telegram_id, message_type, insertion_data: dict | None = None, language=None
):
    await asend_template_telegram_message(
        telegram_id, message_type, insertion_data, language
    )


async def asend_template_telegram_message(
    telegram_id, message_type, insertion_data: dict | None = None, language=None
):
    if telegram_id is None:
        return

    if insertion_data is None:
        insertion_data = {}

    assert message_type in MessageType.values

    template_message = await TemplateTelegramMessage.objects.aget(
        message_type=message_type
    )
    text = template_message.text.get(language)

    for field in template_message.insertion_iter():
        try:
            value = insertion_data[field]
        except KeyError:
            raise ValueError(f"insertion data dict must have {field}")

        if isinstance(value, date):
            value = value.strftime("%d.%m.%Y")
        elif isinstance(value, (float, Decimal)):
            value = round(value, 2)

        text = text.replace(f"{{{field}}}", str(value))

    await asend_telegram_message(telegram_id, text)


@aiogram_async_to_sync
async def send_template_telegram_message_for_many(messages_data: list):
    for message_data in messages_data:
        await asend_template_telegram_message(**message_data)
