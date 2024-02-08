from django.conf import settings
from django.core.management.base import BaseCommand

from apps.telegram.models import (
    TemplateTelegramMessage,
    MessageType,
    INITIAL_MESSAGE_TYPES,
)


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            action="store_true",
            dest="force",
            help="Force update messages",
        )

    def handle(self, *args, **options):
        force_update = bool(options["force"])

        template_message_list = []
        for template_message_type in MessageType.values:
            template_message_text = INITIAL_MESSAGE_TYPES.get(template_message_type)
            if template_message_text is None:
                template_message_text = {
                    code: "Заполните это поле" for code, _ in settings.LANGUAGES
                }

            template_message = TemplateTelegramMessage.objects.filter(
                message_type=template_message_type
            ).first()
            if template_message is None:
                template_message = TemplateTelegramMessage.objects.create(
                    message_type=template_message_type,
                    text=template_message_text,
                )
            elif force_update:
                template_message.text = template_message_text
                template_message.save()

            template_message_list.append(template_message.pk)

        TemplateTelegramMessage.objects.exclude(pk__in=template_message_list).delete()
        print("Success")
