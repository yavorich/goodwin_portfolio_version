from decimal import Decimal
from datetime import date


def get_inserted_text(message, insertion_data, language):
    text = message.text.get(language)

    for field in message.insertion_iter():
        try:
            value = insertion_data[field]
        except KeyError:
            raise ValueError(f"insertion data dict must have {field}")

        if isinstance(value, date):
            value = value.strftime("%d.%m.%Y")
        elif isinstance(value, (float, Decimal)):
            value = round(value, 2)

        text = text.replace(f"{{{field}}}", str(value))

    return text
