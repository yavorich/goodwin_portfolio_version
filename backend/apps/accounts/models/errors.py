from django.db.models import TextChoices, Model, CharField

from core.localized.fields import LocalizedTextField


class ErrorType(TextChoices):
    INCORRECT_VALUE = "incorrect_value", "Неверное значение"
    FILL_REQUIRED = "fill_required", "Обязательно к заполнению"
    INSUFFICIENT_FUNDS = "insufficient_funds", "Недостаточно средств"
    USER_EMAIL_MISMATCH = "user_email_mismatch", "Email не совпадает"
    INVALID_EMAIL = "invalid_email", "Неверный Email"
    INVALID_PASSWORD = "invalid_password", "Неверный пароль"
    USER_NOT_FOUND = "user_not_found", "Пользователь не найден"
    PASSWORD_MISMATCH = "password_mismatch", "Пароли не совпадают"
    STRONG_PASSWORD = "strong_password", "Надёжный пароль"
    SAME_EMAIL = "same_email", "Email существует"
    INVALID_CODE = "invalid_code", "Неверный код"
    FILL_IN_FIELD = "fill_in_field", "Заполните поле"
    EMAIL_AT_SIGN = "email_at_sign", "Email должен содержать @"
    EMAIL_AT_AFTER = "email_at_after", "Адрес email неполный"
    WEAK_PASSWORD = "weak_password", "Слабый пароль"
    MIN_PROGRAM_DEPOSIT = "min_program_deposit", "Минимальный депозит программы"
    MIN_PROGRAM_REPLENISHMENT = (
        "min_program_replenishment",
        "Минимальная сумма пополнения программы",
    )
    MIN_CANCEL_REPLENISHMENT = (
        "min_cancel_replenishment",
        "Минимальный остаток пополнения программы",
    )
    MIN_CANCEL_PROGRAM_DEPOSIT = (
        "min_cancel_program_deposit",
        "Минимальный остаток депозита программы",
    )
    INSUFFICIENT_DEPOSIT = (
        "insufficient_deposit",
        "Сумма закрытия больше депозита",
    )
    INSUFFICIENT_CANCEL_AMOUNT = (
        "insufficient_cancel_amount",
        "Сумма отмены больше суммы пополнения",
    )
    SELF_TRANSFER = "self_transfer", "Перевод самому себе"


DATA_INSERTION = {
    ErrorType.INSUFFICIENT_FUNDS: {"section": "Раздел кошелька"},
    ErrorType.MIN_PROGRAM_DEPOSIT: {"amount": "Cумма в USDT"},
    ErrorType.MIN_PROGRAM_REPLENISHMENT: {"amount": "Cумма в USDT"},
    ErrorType.MIN_CANCEL_REPLENISHMENT: {"amount": "Cумма в USDT"},
    ErrorType.MIN_CANCEL_PROGRAM_DEPOSIT: {"amount": "Cумма в USDT"},
}


INITIAL_MESSAGE_TYPES = {
    ErrorType.INCORRECT_VALUE: dict(
        ru="Введите правильное значение",
        en="Enter the correct value",
        cn="",
    ),
    ErrorType.FILL_REQUIRED: dict(
        ru="Обязательно к заполнению",
        en="Required to fill out",
        cn="",
    ),
    ErrorType.INSUFFICIENT_FUNDS: dict(
        ru="Недостаточно {section} средств",
        en="Not enough {section} funds",
        cn="",
    ),
    ErrorType.USER_EMAIL_MISMATCH: dict(
        ru="Привязанный адрес не совпадает с введённым",
        en="Linked and entered email addresses don't match",
        cn="",
    ),
    ErrorType.INVALID_EMAIL: dict(
        ru="Введите правильный адрес электронной почты",
        en="Enter a valid email address",
        cn="",
    ),
    ErrorType.INVALID_PASSWORD: dict(
        ru="Неверный пароль",
        en="Invalid password",
        cn="",
    ),
    ErrorType.SAME_EMAIL: dict(
        ru="Профиль с такой электронной почтой уже существует",
        en="A profile with the same email already exists",
        cn="",
    ),
    ErrorType.PASSWORD_MISMATCH: dict(
        ru="Пароли не совпадают",
        en="Passwords don't match",
        cn="",
    ),
    ErrorType.INVALID_CODE: dict(
        ru="Неверный код",
        en="Invalid code",
        cn="",
    ),
    ErrorType.USER_NOT_FOUND: dict(
        ru="Пользователь не найден",
        en="User not found",
        cn="",
    ),
    ErrorType.STRONG_PASSWORD: dict(
        ru="Надёжный пароль",
        en="Strong password",
        cn="",
    ),
    ErrorType.WEAK_PASSWORD: dict(
        ru="Слабый пароль",
        en="Weak password",
        cn="",
    ),
    ErrorType.EMAIL_AT_SIGN: dict(
        ru=(
            'Адрес электронной почты должен содержать символ "@". '
            '- В адресе "{email}" отсутствует символ "@".'
        ),
        en=(
            'The email address must contain the "@" symbol. '
            'The "{email}" address does not contain the "@" symbol.'
        ),
        cn="",
    ),
    ErrorType.EMAIL_AT_AFTER: dict(
        ru="Введите часть адреса после символа «@». Адрес «{email}» неполный.",
        en=(
            'Enter the part of the address after the "@" symbol. '
            'The "{email}" address is incomplete.'
        ),
        cn="",
    ),
    ErrorType.FILL_IN_FIELD: dict(
        ru="Заполните это поле",
        en="Fill in this field",
        cn="",
    ),
    ErrorType.MIN_PROGRAM_DEPOSIT: dict(
        ru="Минимальный депозит программы - {amount} USDT",
        en="Minimum program deposit - {amount} USDT",
        cn="",
    ),
    ErrorType.MIN_PROGRAM_REPLENISHMENT: dict(
        ru="Минимальная сумма пополнения программы - {amount} USDT",
        en="Minimum program replenishment amount - {amount} USDT",
        cn="",
    ),
    ErrorType.MIN_CANCEL_REPLENISHMENT: dict(
        ru="Минимальный остаток пополнения программы - {amount} USDT",
        en="Minimum program replenishment amount after cancellation - {amount} USDT",
        cn="",
    ),
    ErrorType.MIN_CANCEL_PROGRAM_DEPOSIT: dict(
        ru="Минимальный депозит программы после частичного закрытия - {amount} USDT",
        en="Minimum program deposit after partial closure - {amount} USDT",
        cn="",
    ),
    ErrorType.INSUFFICIENT_DEPOSIT: dict(
        ru="Недостаточно средств для вывода из программы",
        en="Insufficient program funds to withdraw",
        cn="",
    ),
    ErrorType.INSUFFICIENT_CANCEL_AMOUNT: dict(
        ru="Сумма отмены превышает сумму пополнения",
        en="The cancellation amount exceeds the replenishment amount",
        cn="",
    ),
    ErrorType.SELF_TRANSFER: dict(
        ru="Отправитель и получатель должны отличаться",
        en="Sender and recipient must be different",
        cn="",
    )
}


class ErrorMessage(Model):
    error_type = CharField(choices=ErrorType.choices)

    text = LocalizedTextField("Основной текст")

    class Meta:
        verbose_name = "уведомление"
        verbose_name_plural = "Уведомления об ошибках"

    def __str__(self):
        return self.get_error_type_display()

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
        data_insertions = DATA_INSERTION.get(self.error_type)
        if data_insertions is None:
            return []

        return data_insertions.items()
