# keyboards.py
from bot_state import bot_state
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import PROBLEM_LEVELS, PROBLEM_SERVICES


def create_main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="📸 JIRA/Confluence"),
        KeyboardButton(text="📢 Сообщить"),
        KeyboardButton(text="🛂 Управлять"),
        KeyboardButton(text="📕 Текущие события"),
        KeyboardButton(text="ℹ️ Помощь")
    )
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)


def create_view_selection_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="📅 Календарь работ"),
        KeyboardButton(text="🔍 Посмотреть JIRA"),
        KeyboardButton(text="🌐 Посмотреть Confluence"),
        KeyboardButton(text="❌ Отмена")
    )
    builder.adjust(1, 1, 1)
    return builder.as_markup(resize_keyboard=True)


def create_message_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🚨 Сбой", callback_data="message_type_alarm"),
        InlineKeyboardButton(text="🔧 Работа", callback_data="message_type_maintenance")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Обычное сообщение", callback_data="message_type_regular")
    )
    return builder.as_markup()


def create_cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def create_yes_no_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="✅ Да"),
        KeyboardButton(text="❌ Нет")
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def create_confirmation_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="Отправить"),
        KeyboardButton(text="Не отправлять")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


# --- Изменённые функции для работы команды управлять---

def create_action_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🛑 Остановить", callback_data="action_stop"),
        InlineKeyboardButton(text="⏳ Продлить", callback_data="action_extend")
    )
    return builder.as_markup()


def create_extension_time_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ 30 мин", callback_data="extend_30_min"),
        InlineKeyboardButton(text="➕ 1 час", callback_data="extend_1_hour"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="extend_cancel")
    )
    return builder.as_markup()


def create_alarm_selection_keyboard(alarm_ids: list = None):
    builder = InlineKeyboardBuilder()
    alarm_ids = alarm_ids or []
    if not alarm_ids:
        builder.row(InlineKeyboardButton(text="Нет активных сбоев", callback_data="select_no_alarms"))
    else:
        for alarm_id in alarm_ids:
            alarm = bot_state.active_alarms.get(alarm_id)
            if not alarm:
                continue
            btn_text = f"{alarm_id}: {alarm['issue'][:20]}..."
            builder.row(InlineKeyboardButton(text=btn_text, callback_data=f"select_alarm_{alarm_id}"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="select_cancel"))
    return builder.as_markup()


def create_stop_type_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🚨 Сбой 🚨"),
        KeyboardButton(text="🔧 Работа 🔧")
    )
    builder.row(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def create_maintenance_selection_keyboard(maintenances: dict):
    builder = InlineKeyboardBuilder()
    for work_id, data in maintenances.items():
        owner_info = f" (от {data['user_id']})" if 'user_id' in data else ""
        btn_text = f"{work_id}: {data['description'][:20]}...{owner_info}"
        builder.row(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"select_maintenance_{work_id}"
            )
        )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="select_cancel"))
    return builder.as_markup()

def create_reminder_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, продлеваем", callback_data="reminder_extend"),
        InlineKeyboardButton(text="❌ Нет, останавливаем", callback_data="reminder_stop")
    )
    return builder.as_markup()

def create_event_list_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🚨 Сбои", callback_data="show_alarms")
    builder.button(text="🔧 Работы", callback_data="show_maintenances")
    builder.button(text="❌ Закрыть", callback_data="close_selection")
    builder.adjust(1)
    return builder.as_markup()

def create_level_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора уровня проблемы."""
    builder = InlineKeyboardBuilder()
    for i, level in enumerate(PROBLEM_LEVELS):
        builder.button(text=level, callback_data=f"lvl_{i}")
    builder.button(text="Отмена", callback_data="cancel")
    builder.adjust(1)  # Размещаем кнопки в один столбец
    return builder.as_markup()

def create_service_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора сервиса."""
    builder = InlineKeyboardBuilder()
    for i, service in enumerate(PROBLEM_SERVICES):
        builder.button(text=service, callback_data=f"svc_{i}")
    builder.button(text="Отмена", callback_data="cancel")
    builder.adjust(1)  # Размещаем кнопки в один столбец
    return builder.as_markup()