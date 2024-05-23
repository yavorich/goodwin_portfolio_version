from decimal import Decimal
from datetime import date

from django.utils import translation
from rest_framework.exceptions import ValidationError

from apps.accounts.models import ErrorType, ErrorMessage


def get_error(error_type: ErrorType, insertions: dict | None = None, language=None):
    insertion_data = insertions or {}

    template_message = ErrorMessage.objects.get(error_type=error_type)
    language = language or translation.get_language()
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

    raise ValidationError(detail=text)
