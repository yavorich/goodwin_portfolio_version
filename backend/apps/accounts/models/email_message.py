from django.db.models import TextChoices, Model, CharField

from core.localized.fields import LocalizedTextField


class EmailMessageType(TextChoices):
    AUTH_CONFIRM = "auth_confirm", "Подтверждение почты"
    PASSWORD_RECOVERY = "password_recovery", "Восстановление пароля"
    PASSWORD_CHANGE = "password_change", "Изменение пароля"
    SETTINGS_CHANGE = "settings_change", "Изменение настроек профиля"
    EMAIL_CHANGE = "email_change", "Изменение почты"
    OPERATION_CONFIRM = "operation_confirm", "Подтверждение операции"


DATA_INSERTION = {
    EmailMessageType.AUTH_CONFIRM: {"code": "Код подтверждения"},
    EmailMessageType.PASSWORD_RECOVERY: {"full_name": "Полное имя пользователя"},
    EmailMessageType.PASSWORD_CHANGE: {"code": "Код подтверждения"},
    EmailMessageType.SETTINGS_CHANGE: {"code": "Код подтверждения"},
    EmailMessageType.EMAIL_CHANGE: {"code": "Код подтверждения"},
    EmailMessageType.OPERATION_CONFIRM: {"code": "Код подтверждения"},
}

TEMPLATE_TITLE = {
    EmailMessageType.AUTH_CONFIRM: dict(
        ru="GDW Finance - Подтверждение электронной почты",
        en="GDW Finance - Email confirmation",
        cn="",
    ),
    EmailMessageType.PASSWORD_RECOVERY: dict(
        ru="GDW Finance - Восстановление пароля",
        en="GDW Finance - Password recovery",
        cn="",
    ),
    EmailMessageType.PASSWORD_CHANGE: dict(
        ru="GDW Finance - Подтверждение изменения пароля",
        en="GDW Finance - Password change confirmation",
        cn="",
    ),
    EmailMessageType.SETTINGS_CHANGE: dict(
        ru="GDW Finance - Подтверждение изменения настроек профиля",
        en="GDW Finance - Profile settings change confirmation",
        cn="",
    ),
    EmailMessageType.EMAIL_CHANGE: dict(
        ru="GDW Finance - Подтверждение смены адреса электронной почты",
        en="GDW Finance - Email address change confirmation",
        cn="",
    ),
    EmailMessageType.OPERATION_CONFIRM: dict(
        ru="GDW Finance - Подтверждение операции",
        en="GDW Finance - Operation confirmation",
        cn="",
    ),
}
TEMPLATE_TEXT = {
    EmailMessageType.AUTH_CONFIRM: dict(
        ru="Здравствуйте!\nВаш код для подтверждения почты: {code}",
        en="Hello!\nYour email confirmation code: {code}",
        cn="",
    ),
    EmailMessageType.PASSWORD_RECOVERY: dict(
        ru=(
            "Здравствуйте, {full_name}!\n"
            "Был отправлен запрос на сброс пароля для вашего аккаунта. "
            "Если это сделали не вы, проигнорируйте данное сообщение "
            "(Эта ссылка действует 1 раз и в течение 24 часов)"
        ),
        en=(
            "Hello, {full_name}!\n"
            "A request has been sent to reset the password "
            "for your account. If you did not do this, ignore this message "
            "(This link is valid once and for 24 hours)"
        ),
        cn="",
    ),
    EmailMessageType.PASSWORD_CHANGE: dict(
        ru="Здравствуйте!\nВаш код для подтверждения смены пароля: {code}",
        en="Hello!\nYour code to confirm the password change: {code}",
        cn="",
    ),
    EmailMessageType.SETTINGS_CHANGE: dict(
        ru="Здравствуйте!\nВаш код для подтверждения изменения настроек: {code}",
        en="Hello!\nYour code to confirm the settings change: {code}",
        cn="",
    ),
    EmailMessageType.EMAIL_CHANGE: dict(
        ru=(
            "Здравствуйте!\nВаш код для подтверждения смены "
            "адреса электронной почты: {code}"
        ),
        en="Hello!\nYour code to confirm the email change: {code}",
        cn="",
    ),
    EmailMessageType.OPERATION_CONFIRM: dict(
        ru="Здравствуйте!\nВаш код для подтверждения операции: {code}",
        en="Hello!\nYour code to confirm the operation: {code}",
        cn="",
    ),
}


class EmailMessage(Model):
    message_type = CharField(choices=EmailMessageType.choices)

    title = LocalizedTextField("Заголовок")
    text = LocalizedTextField("Основной текст")

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "Шаблоны email-сообщений"

    def __str__(self):
        return self.get_message_type_display()

    @property
    def data_insertions_pretty(self):
        insertions = self._get_insertions()
        header = (
            "Добавьте в текст сообщения в виде: {название}\n\n"
            "Доступные параметры (название: описание)\n\n"
        )
        parameters = "\n".join(
            (f"{slug}: {description}" for slug, description in insertions)
        )
        return header + parameters if len(parameters) > 0 else "-"

    def insertion_iter(self):
        return (slug for slug, description in self._get_insertions())

    def _get_insertions(self):
        data_insertions = DATA_INSERTION.get(self.message_type)
        if data_insertions is None:
            return []

        return data_insertions.items()
