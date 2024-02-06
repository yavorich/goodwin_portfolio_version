from django.db.models import TextChoices


class MessageType(TextChoices):
    GREETINGS = "greetings", "Приветствие"
    NOTIFY_CONNECTED = "notify_connected", "Уведомления подключены"
    NOTIFY_DISCONNECTED = "notify_disconnected", "Уведомления отключены"
    PROGRAM_START = "PROGRAM_START", "Запуск программы"
    PROGRAM_STARTED = "PROGRAM_STARTED", "Программа запущена"
    PROGRAM_CLOSING = "PROGRAM_CLOSING", "Закрытие программы"
    FROZEN_AVAILABLE = "frozen_available", "Доступны замороженные активы"
    START_WITH_REPLENISHMENT = "start_with_replenishment", "Запуск с учетом пополнения"
    CANCELING_PROGRAM_REPLENISHMENT = (
        "CANCELING_PROGRAM_REPLENISHMENT",
        "Отмена пополнения программы",
    )
    PREMATURE_DEFROST = "premature_defrost", "Досрочная разморозка"
    WITHDRAWAL_REQUEST = "withdrawal_request", "Заявка на вывод"
    SUCCESSFUL_TRANSFER = "successful_transfer", "Успешный перевод"
    TRANSFER_REJECTED = "transfer_rejected", "Перевод отклонен"
    INTERNAL_TRANSFER_FOR_SENDER = (
        "internal_transfer_for_sender",
        "Внутренний перевод (для отправителя)",
    )
    INTERNAL_TRANSFER_FOR_RECIPIENT = (
        "internal_transfer_for_recipient",
        "Внутренний перевод (для получателя)",
    )
    PROGRAM_PROFIT = "program_profit", "Прибыль по программе"
    # PROGRAM_LOSS = "program_loss", "Убыток по программе"


DATA_INSERTION = {
    MessageType.PROGRAM_START: {
        "program_name": "Название программы",
        "start_date": "Дата начала торговли",
        "underlying_asset": "Размер базового актива (USDT)",
        "email": "Почта пользователя",
    },
    MessageType.PROGRAM_STARTED: {
        "program_name": "Название программы",
        "underlying_asset": "Размер базового актива (USDT)",
        "email": "Почта пользователя",
    },
    MessageType.PROGRAM_CLOSING: {
        "program_name": "Название программы",
        "defrost_date": "Дата разморозки",
        "extra_fee_percent": "Процент комиссии Extra fee",
        "email": "Почта пользователя",
    },
    MessageType.FROZEN_AVAILABLE: {
        "frozen_date": "Дата заморозки",
        "frozen_amount": "Размер заморозки (USDT)",
    },
    MessageType.START_WITH_REPLENISHMENT: {
        "program_name": "Название программы",
    },
    MessageType.CANCELING_PROGRAM_REPLENISHMENT: {
        "program_name": "Название программы",
        "available_date": "Дата возможного вывода средств",
        "extra_fee_percent": "Процент комиссии Extra fee",
        "email": "Почта пользователя",
    },
    MessageType.PREMATURE_DEFROST: {
        "amount": "Сумма вывода без вычета Extra fee (USDT)",
        "extra_fee_percent": "Процент комиссии Extra fee",
        "extra_fee_amount": "Размер Extra fee для суммы вывода (USDT)",
        "amount_with_extra_fee": "Сумма вывода с вычетом Extra fee (USDT)",
    },
    MessageType.WITHDRAWAL_REQUEST: {
        "amount": "Сумма списания с Wallet (USDT)",
        "commission_amount": "Сумма транзакционной комиссии (USDT)",
        "amount_with_commission": "Сумма перевода (USDT)",
        "transfer address": "Адрес перевода",
        "email": "Почта пользователя",
    },
    MessageType.SUCCESSFUL_TRANSFER: {
        "amount": "Сумма списания с Wallet (USDT)",
        "commission_amount": "Сумма транзакционной комиссии (USDT)",
        "amount_with_commission": "Сумма перевода (USDT)",
        "transfer address": "Адрес перевода",
        "email": "Почта пользователя",
    },
    MessageType.TRANSFER_REJECTED: {
        "amount": "Сумма списания с Wallet (USDT)",
        "commission_amount": "Сумма транзакционной комиссии (USDT)",
        "amount_with_commission": "Сумма перевода (USDT)",
        "transfer address": "Адрес перевода",
        "email": "Почта пользователя",
    },
    MessageType.INTERNAL_TRANSFER_FOR_SENDER: {
        "user_id": "ID пользователя",
        "amount": "Сумма перевода (USDT)",
        "email": "Почта пользователя",
    },
    MessageType.INTERNAL_TRANSFER_FOR_RECIPIENT: {
        "user_id": "ID пользователя",
        "amount": "Сумма перевода (USDT)",
    },
    MessageType.PROGRAM_PROFIT: {
        "program_name": "Название программы",
        "yesterday_profit": "Прибыль за вчерашний торговый день (USDT)",
        "yesterday_profit_percent": "Прибыль за вчерашний торговый день в процентах",
        "all_profit": "Общая прибыль (USDT)",
        "all_profit_percent": "Общая прибыль в процентах",
        "underlying_asset": "Размер базового актива (USDT)",
        "email": "Почта пользователя",
    },
}


# по данному шаблону создаются сообщения с помощью команды
# python manage.py create_template_telegram_messages
INITIAL_MESSAGE_TYPES = {
    MessageType.GREETINGS: {
        "ru": (
            "Здравствуй, инвестор! Рад видеть тебя в команде GDW Finance!\n"
            "Я - GDW_bot, помогу тебе быть в курсе всего, что происходит в твоем "
            "личном кабинете GDW Finance.\n"
            "GDW_bot будет присылать Вам следующие уведомления:\n"
            "- Пополнение/вывод/перевод баланса\n"
            "- Запуск и завершение инвестиционных программ\n"
            "- Начисление прибыли по инвестиционным программам\n"
            "- Изменение инвестиционных программ\n"
            "Но для того, чтобы я начал на тебя работать, меня нужно привязаться к "
            "твоему аккаунту. Для этого нужно подключить меня в профиле личного "
            "кабинета."
        )
    },
    MessageType.NOTIFY_CONNECTED: {
        "ru": "Вы были успешно подключены к Telegram уведомлениям!",
    },
    MessageType.NOTIFY_DISCONNECTED: {
        "ru": "Telegram уведомления успешно отключены!",
    },
    MessageType.PROGRAM_START: {
        "ru": (
            "#Запуск программы {program_name}\n"
            "Дата начала торговли: {start_date}\n"
            "Базовый актив: {underlying_asset} USDT\n\n"
            "Логин: {email}"
        )
    },
    MessageType.PROGRAM_STARTED: {
        "ru": (
            "Программа {program_name} запущена!\n"
            "Базовый актив: {underlying_asset} USDT\n\n"
            "Логин: {email}"
        )
    },
    MessageType.PROGRAM_CLOSING: {
        "ru": (
            "#Закрытие_программы\n"
            "Принята заявка на закрытие программы {program_name} на сумму 1000 USDT\n\n"
            "Вывод основного актива программы будет возможен {defrost_date} г\n\n"
            "Вы можете воспользоваться досрочной разморозкой, уплатив при этом "
            "комиссию Extra fee – {extra_fee_percent} %\n\n"
            "Логин: {email}"
        )
    },
    MessageType.FROZEN_AVAILABLE: {
        "ru": (
            "Замороженные активы от {frozen_date} г. в размере {frozen_amount} USDT "
            "доступны к выводу."
        )
    },
    MessageType.START_WITH_REPLENISHMENT: {
        "ru": "Программа {program_name} запущена с учетом пополнения!"
    },
    MessageType.CANCELING_PROGRAM_REPLENISHMENT: {
        "ru": (
            "#Отмена пополнение программы {program_name} на сумму {amount} USDT\n\n"
            "Вывод средств будет возможен {available_date} г\n\n"
            "Вы можете воспользоваться досрочной разморозкой, уплатив при этом "
            "комиссию Extra fee – {extra_fee_percent} %\n\n"
            "Логин: {email}"
        )
    },
    MessageType.PREMATURE_DEFROST: {
        "ru": (
            "#Досрочная_разморозка:\n"
            "Заявка на разморозку активов на сумму {amount} USDT исполнена.\n"
            "Удержана комиссия Extra fee {extra_fee_percent} %: "
            "{extra_fee_amount} USDT\n"
            "Сумма в размере {amount_with_extra_fee} USDT доступна к выводу"
        )
    },
    MessageType.WITHDRAWAL_REQUEST: {
        "ru": (
            "Получена заявка на вывод:\n\n"
            "Сумма списания с Wallet: {amount} USDT\n"
            "Сумма транзакционной комиссии: {commission_amount} USDT\n"
            "Сумма перевода: {amount_with_commission} USDT\n"
            "Адрес перевода: {transfer address}\n\n"
            "Логин: {email}"
        )
    },
    MessageType.SUCCESSFUL_TRANSFER: {
        "ru": (
            "#Перевод выполнен успешно:\n\n"
            "Сумма списания с Wallet: {amount} USDT\n"
            "Сумма транзакционной комиссии: {commission_amount} USDT\n"
            "Сумма перевода: {amount_with_commission} USDT\n"
            "Адрес перевода: {transfer address}\n\n"
            "Логин: {email}"
        )
    },
    MessageType.TRANSFER_REJECTED: {
        "ru": (
            "#Перевод отклонен, свяжитесь с тех поддержкой через мессенджеры, "
            "указанные в личном кабинете:\n\n"
            "Сумма списания с Wallet: {amount} USDT\n"
            "Сумма транзакционной комиссии: {commission_amount} USDT\n"
            "Сумма перевода: {amount_with_commission} USDT\n"
            "Адрес перевода: {transfer address}\n\n"
            "Логин: {email}"
        )
    },
    MessageType.INTERNAL_TRANSFER_FOR_SENDER: {
        "ru": (
            "#Внутренний перевод.\n"
            "Перевод клиенту GDW ID{user_id} сумму {amount} USDT исполнен.\n"
            "Логин: {email}"
        )
    },
    MessageType.INTERNAL_TRANSFER_FOR_RECIPIENT: {
        "ru": (
            "#Внутренний перевод.\n"
            "Поступление от аккаунта ID{user_id} на сумму {amount} USDT.\n"
            "Сумма зачислена в раздел «Заморожено»."
        )
    },
    MessageType.PROGRAM_PROFIT: {
        "ru": (
            "#Прибыль по программе {program_name}:\n\n"
            "Прибыль за вчерашний торговый день: {yesterday_profit} USDT "
            "({yesterday_profit_percent} %)\n"
            "Общая прибыль {all_profit} USDT ({all_profit_percent} %)\n"
            "Базовый актив программы {program_name}: {underlying_asset} USDT\n\n"
            "*Доход инвестора указан за вычетом Success fee и Management Fee\n\n"
            "Логин: {email}"
        )
    },
}
