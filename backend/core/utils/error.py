from django.utils import translation
from rest_framework.exceptions import ValidationError

from apps.accounts.models import ErrorMessageType, ErrorMessage
from .get_inserted_text import get_inserted_text


def get_error(
    error_type: ErrorMessageType, insertions: dict | None = None, language=None
):
    insertion_data = insertions or {}

    template_message = ErrorMessage.objects.get(error_type=error_type)
    language = language or translation.get_language()
    text = get_inserted_text(template_message, insertion_data, language)

    raise ValidationError(detail=text)
