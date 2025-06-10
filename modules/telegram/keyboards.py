"""
Клавиатуры для Telegram бота
"""
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Списки опций
PROBLEM_LEVELS = [
    "Замедление работы сервиса",
    "Полная недоступность сервиса",
    "Частичная недоступность сервиса",
    "Проблемы в работе сервиса",
    "Потенциальная недоступность сервиса"
]

PROBLEM_SERVICES = [
    "Naumen", "Электронная почта", "УТЦ", "УТ Юнион", "1С УТ СПБ", "1С УТ СЗФО",
    "1С УТ МСК", "1С ЦФС", "УТ СПБ+УТ СЗФО+ УТ МСК", "LMS", "Проблема с обменами",
    "Сеть и интернет 1 подразделения", "Удалённый рабочий стол RDP (trm)",
    "Удалённый рабочий стол RDP для КЦ (retrm)", "VPN офисный", "VPN ДО КЦ",
    "Стационарная телефония", "Мобильная телефония", "Сетевое хранилище (Диск Х)",
    "Сайт Petrovich.ru", "Чат на сайте", "Jira", "Confluence", "Petlocal.ru",
    "Электроэнергия", "Телеопти/Май тайм", "Сервис оплаты", "Jira + Confluence",
    "b2b.stdp.ru", "Skype for business(Lync)", "DocsVision (DV)", "УТ СПБ",
    "ЗУП", "HR-Link", "WMS", "Мобильное приложение", "Другое"
]

NAUMEN_FAILURE_TYPES = [
    "Голосовой канал", "Авторизация", "Softphone", "Анкета", "Кейсы с сайта",
    "Почтовый канал", "Чат (VK, WA, Telegram, Webim)", "Отчёты", "Другое"
]

STREAM_1C_OPTIONS = [
    "Интеграция", "Коммерция", "Маркетинг", "ОПТ", "ПиКК", "Розница (СТЦ/КЦ)",
    "Сервисы оплат", "Складская логистика", "Транспортная логистика",
    "Финансы", "ЭДО"
]

INFLUENCE_OPTIONS = ["Клиенты", "Бизнес-функция", "Сотрудники"]

def get_main_keyboard():
    """Создает основную клавиатуру"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🚨 Создать задачу FA"))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_keyboard_from_list(options, add_cancel=True, is_optional=False):
    """Создает клавиатуру из списка опций"""
    builder = ReplyKeyboardBuilder()
    for option in options:
        builder.add(KeyboardButton(text=option))
    if add_cancel:
        if is_optional:
            builder.add(KeyboardButton(text="Не заполнять"))
        builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True) 