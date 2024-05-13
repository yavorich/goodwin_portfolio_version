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
    PROGRAM_LOSS = "program_loss", "Убыток по программе"


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
        "amount": "Сумма закрытия",
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
    MessageType.PROGRAM_LOSS: {
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
        ),
        "en": (
            "Hello investor! Glad to see you on the GDW Finance team!\n"
            "I am GDW_bot, I will help you keep abreast of everything that happens in "
            "your personal account GDW Finance.\n"
            "GDW_bot will send you the following notifications:\n"
            "- Replenishment/withdrawal/transfer of balance\n"
            "- Launch and completion of investment programs\n"
            "- Accrual of profit under investment programs\n"
            "- Changes in investment programs\n"
            "But in order for me to start working for you, I need to be linked to "
            "your account. To do this, you need to connect me in your personal "
            "account profile."
        ),
        "cn": (
            "投资者您好! 很高兴在 GDW 财务团队见到您!\n"
            "我是 GDW_bot, 我将帮助您及时了解您的 GDW Finance 个人账户中发生的一切.\n"
            "GDW_bot 将向您发送以下通知:\n"
            "- 充值/提款/余额转移\n"
            "- 投资计划的启动和完成\n"
            "- 投资计划下的应计利润\n"
            "- 投资计划的变化\n"
            "但为了让我开始为您工作, 我需要链接到您的帐户. 为此, 您需要在您的个人帐户资料中连接我."
        ),
    },
    MessageType.NOTIFY_CONNECTED: {
        "ru": "Вы были успешно подключены к Telegram уведомлениям!",
        "en": "You have been successfully connected to Telegram notifications!",
        "cn": "您已成功连接到 Telegram 通知!",
    },
    MessageType.NOTIFY_DISCONNECTED: {
        "ru": "Telegram уведомления успешно отключены!",
        "en": "Telegram notifications successfully disabled!",
        "cn": "电报通知已成功禁用!",
    },
    MessageType.PROGRAM_START: {
        "ru": (
            "#Запуск программы {program_name}\n"
            "Дата начала торговли: {start_date}\n"
            "Базовый актив: {underlying_asset} USDT\n\n"
            "Логин: {email}"
        ),
        "en": (
            "#Starting the program {program_name}\n"
            "Trading start date: {start_date}\n"
            "Underlying asset: {underlying_asset} USDT\n\n"
            "Login: {email}"
        ),
        "cn": (
            "#启动程序 {program_name}\n"
            "交易开始日期: {start_date}\n"
            "标的资产: {underlying_asset} USDT\n\n"
            "登录: {email}"
        ),
    },
    MessageType.PROGRAM_STARTED: {
        "ru": (
            "Программа {program_name} запущена!\n"
            "Базовый актив: {underlying_asset} USDT\n\n"
            "Логин: {email}"
        ),
        "en": (
            "Program {program_name} is running!\n"
            "Underlying asset: {underlying_asset} USDT\n\n"
            "Login: {email}"
        ),
        "cn": (
            "程序 {program_name} 推出!\n标的资产: {underlying_asset} USDT\n\n登录: {email}"
        ),
    },
    MessageType.PROGRAM_CLOSING: {
        "ru": (
            "#Закрытие программы\n"
            "Принята заявка на закрытие программы {program_name} на сумму "
            "{amount} USDT\n\n"
            "Вывод основного актива программы будет возможен {defrost_date} г\n\n"
            "Вы можете воспользоваться досрочной разморозкой, уплатив при этом "
            "комиссию Extra fee – {extra_fee_percent} %\n\n"
            "Логин: {email}"
        ),
        "en": (
            "#Closing the program\n"
            "An application has been accepted to close the program {program_name} "
            "for the amount {amount} USDT\n\n"
            "Withdrawal of the main asset of the program will be possible at "
            "{defrost_date}\n\n"
            "You can take advantage of early defrosting by paying a "
            "Extra fee – {extra_fee_percent} %\n\n"
            "Login: {email}"
        ),
        "cn": (
            "#关闭程序\n"
            "关闭该计划的申请已被接受 {program_name} 对于金额 {amount} USDT\n\n"
            "可以撤回该计划的主要资产 {defrost_date} г\n\n"
            "您可以付费使用提前除霜 Extra fee – {extra_fee_percent} %\n\n"
            "登录: {email}"
        ),
    },
    MessageType.FROZEN_AVAILABLE: {
        "ru": (
            "Замороженные активы от {frozen_date} г. в размере {frozen_amount} USDT "
            "доступны к выводу."
        ),
        "en": (
            "Frozen assets from {frozen_date} in the amount of {frozen_amount} USDT "
            "are available for withdrawal."
        ),
        "cn": "冻结资产来自 {frozen_date} 年 以 {frozen_amount} USDT 可提现.",
    },
    MessageType.START_WITH_REPLENISHMENT: {
        "ru": "Программа {program_name} запущена с учетом пополнения!",
        "en": "Program {program_name} launched taking into account replenishment!",
        "cn": "程序 {program_name} 考虑到补货而推出!",
    },
    MessageType.CANCELING_PROGRAM_REPLENISHMENT: {
        "ru": (
            "#Отмена пополнение программы {program_name} на сумму {amount} USDT\n\n"
            "Вывод средств будет возможен {available_date} г\n\n"
            "Вы можете воспользоваться досрочной разморозкой, уплатив при этом "
            "комиссию Extra fee – {extra_fee_percent} %\n\n"
            "Логин: {email}"
        ),
        "en": (
            "#Cancel replenishment of program {program_name} by the amount "
            "{amount} USDT\n\n"
            "Withdrawals will be possible on {available_date}\n\n"
            "You can take advantage of early defrosting by paying a "
            "Extra fee – {extra_fee_percent} %\n\n"
            "Login: {email}"
        ),
        "cn": (
            "#取消补货计划 {program_name} 对于金额 {amount} USDT\n\n"
            "可以提款 {available_date} 年\n\n"
            "您可以付费使用提前除霜 Extra fee – {extra_fee_percent} %\n\n"
            "登录: {email}"
        ),
    },
    MessageType.PREMATURE_DEFROST: {
        "ru": (
            "#Досрочная разморозка:\n"
            "Заявка на разморозку активов на сумму {amount} USDT исполнена.\n"
            "Удержана комиссия Extra fee {extra_fee_percent} %: "
            "{extra_fee_amount} USDT\n"
            "Сумма в размере {amount_with_extra_fee} USDT доступна к выводу"
        ),
        "en": (
            "#Early defrosting:\n"
            "The request to unfreeze assets in the amount of {amount} USDT has been "
            "completed.\n"
            "Commission withheld Extra fee {extra_fee_percent} %: "
            "{extra_fee_amount} USDT\n"
            "An amount of {amount_with_extra_fee} USDT is available for withdrawal"
        ),
        "cn": (
            "#提早除霜:\n"
            "申请解冻资产 {amount} USDT 实现了.\n"
            "扣留佣金 Extra fee {extra_fee_percent} %: {extra_fee_amount} USDT\n"
            "总金额 {amount_with_extra_fee} USDT 可提现"
        ),
    },
    MessageType.WITHDRAWAL_REQUEST: {
        "ru": (
            "Получена заявка на вывод:\n\n"
            "Сумма списания с Wallet: {amount} USDT\n"
            "Сумма транзакционной комиссии: {commission_amount} USDT\n"
            "Сумма перевода: {amount_with_commission} USDT\n"
            "Адрес перевода: {transfer_address} \n\n"
            "Логин: {email}"
        ),
        "en": (
            "Request for withdrawal received:\n\n"
            "Amount debited from Wallet: {amount} USDT\n"
            "Transaction fee amount: {commission_amount} USDT\n"
            "Transfer amount: {amount_with_commission} USDT\n"
            "Transfer address: {transfer address}\n\n"
            "Login: {email}"
        ),
        "cn": (
            "收到提款请求:\n\n"
            "核销金额 Wallet: {amount} USDT\n"
            "交易手续费金额: {commission_amount} USDT\n"
            "转账金额: {amount_with_commission} USDT\n"
            "转账地址: {transfer address}\n\n"
            "登录: {email}"
        ),
    },
    MessageType.SUCCESSFUL_TRANSFER: {
        "ru": (
            "#Перевод выполнен успешно:\n\n"
            "Сумма списания с Wallet: {amount} USDT\n"
            "Сумма транзакционной комиссии: {commission_amount} USDT\n"
            "Сумма перевода: {amount_with_commission} USDT\n"
            "Адрес перевода: {transfer_address} \n\n"
            "Логин: {email}"
        ),
        "en": (
            "#Translation completed successfully:\n\n"
            "Amount debited from Wallet: {amount} USDT\n"
            "Transaction fee amount: {commission_amount} USDT\n"
            "Transfer amount: {amount_with_commission} USDT\n"
            "Transfer address: {transfer address}\n\n"
            "Login: {email}"
        ),
        "cn": (
            "#翻译成功完成:\n\n"
            "核销金额 Wallet: {amount} USDT\n"
            "交易手续费金额: {commission_amount} USDT\n"
            "转账金额: {amount_with_commission} USDT\n"
            "转账地址: {transfer address}\n\n"
            "登录: {email}"
        ),
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
        ),
        "en": (
            "#The transfer was rejected, contact technical support via the messengers "
            "specified in your personal account:\n\n"
            "Amount debited from Wallet: {amount} USDT\n"
            "Transaction fee amount: {commission_amount} USDT\n"
            "Transfer amount: {amount_with_commission} USDT\n"
            "Transfer address: {transfer address}\n\n"
            "Login: {email}"
        ),
        "cn": (
            "#转账被拒绝, 请通过您个人账户指定的Messenger联系技术支持:\n\n"
            "核销金额 Wallet: {amount} USDT\n"
            "交易手续费金额: {commission_amount} USDT\n"
            "转账金额: {amount_with_commission} USDT\n"
            "转账地址: {transfer address}\n\n"
            "登录: {email}"
        ),
    },
    MessageType.INTERNAL_TRANSFER_FOR_SENDER: {
        "ru": (
            "#Внутренний перевод.\n"
            "Перевод клиенту GDW ID{user_id} сумму {amount} USDT исполнен.\n"
            "Логин: {email}"
        ),
        "en": (
            "#Internal transfer.\n"
            "Transfer to client GDW ID{user_id} for the amount {amount} USDT "
            "has been completed.\n"
            "Login: {email}"
        ),
        "cn": (
            "##内部转会.\n"
            "转给客户 GDW ID{user_id} 对于金额 {amount} USDT 实现了.\n"
            "登录: {email}"
        ),
    },
    MessageType.INTERNAL_TRANSFER_FOR_RECIPIENT: {
        "ru": (
            "#Внутренний перевод.\n"
            "Поступление от аккаунта ID{user_id} на сумму {amount} USDT.\n"
            "Сумма зачислена в раздел «Заморожено»."
        ),
        "en": (
            "#Internal transfer.\n"
            "Receipt from account ID{user_id} for the amount {amount} USDT.\n"
            "The amount is credited to the “Frozen” section."
        ),
        "cn": "#内部转会.\n帐户收据 ID{user_id} 对于金额 {amount} USDT.\n金额记入“冻结”部分.",
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
        ),
        "en": (
            "#Profit under the program {program_name}:\n\n"
            "Profit for yesterday's trading day: {yesterday_profit} USDT "
            "({yesterday_profit_percent} %)\n"
            "Total profit {all_profit} USDT ({all_profit_percent} %)\n"
            "Basic asset of the program {program_name}: {underlying_asset} USDT\n\n"
            "*The investor's income is shown minus Success fee and Management Fee\n\n"
            "Login: {email}"
        ),
        "cn": (
            "#该计划下的利润 {program_name}:\n\n"
            "昨天交易日盈利: {yesterday_profit} USDT ({yesterday_profit_percent} %)\n"
            "利润总额 {all_profit} USDT ({all_profit_percent} %)\n"
            "该计划的基本资产 {program_name}: {underlying_asset} USDT\n\n"
            "*投资者的收入显示为负 Success fee 和 Management Fee\n\n"
            "登录: {email}"
        ),
    },
    MessageType.PROGRAM_LOSS: {
        "ru": (
            "Прибыль по программе {program_name}:\n\n"
            "Прибыль за вчерашний торговый день: {yesterday_profit} USDT "
            "({yesterday_profit_percent} %)\n"
            "Общая прибыль {all_profit} USDT ({all_profit_percent} %)\n"
            "Базовый актив программы {program_name}: {underlying_asset} USDT\n\n"
            "*Доход инвестора указан за вычетом Success fee и Management Fee\n\n"
            "Логин: {email} \n"
            "(В случае убытка за торговую сессию, минус списывается с базового актива)"
        ),
        "en": (
            "Profit under the program {program_name}:\n\n"
            "Profit for yesterday's trading day: {yesterday_profit} USDT "
            "({yesterday_profit_percent} %)\n"
            "Total profit {all_profit} USDT ({all_profit_percent} %)\n"
            "Basic asset of the program {program_name}: {underlying_asset} USDT\n\n"
            "*The investor's income is shown minus Success fee and Management Fee\n\n"
            "Login: {email} \n"
            "(In case of a loss during a trading session, the minus is written off "
            "from the underlying asset)"
        ),
        "cn": (
            "该计划下的利润 {program_name}:\n\n"
            "昨天交易日盈利: {yesterday_profit} USDT ({yesterday_profit_percent} %)\n"
            "利润总额 {all_profit} USDT ({all_profit_percent} %)\n"
            "该计划的基本资产 {program_name}: {underlying_asset} USDT\n\n"
            "*投资者的收入显示为负 Success fee 和 Management Fee\n\n"
            "登录: {email} \n"
            "(如果交易期间出现亏损，则从标的资产中冲销减额)"
        ),
    },
}
