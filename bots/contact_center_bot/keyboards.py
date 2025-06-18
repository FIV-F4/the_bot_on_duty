"""
Клавиатуры для бота контакт-центра.
"""
from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def create_main_keyboard():
    """Создает основную клавиатуру."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🔧 Техническая неполадка"))
    builder.add(KeyboardButton(text="🏥 Больничный"))
    builder.add(KeyboardButton(text="ℹ️ Помощь"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def create_cancel_keyboard():
    """Создает клавиатуру с кнопкой отмены."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)

def create_problem_side_keyboard():
    """Создает клавиатуру для выбора стороны проблемы."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="👤 Проблема на стороне оператора"))
    builder.add(KeyboardButton(text="🏢 Проблема со стороны компании"))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def create_confirm_keyboard():
    """Создает клавиатуру для подтверждения."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Подтвердить"))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def create_yes_no_keyboard():
    """Создает клавиатуру с да/нет."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Да"))
    builder.add(KeyboardButton(text="❌ Нет"))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def create_for_who_keyboard():
    """Создает клавиатуру для выбора на кого открыт больничный."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="👤 По уходу за больным"))
    builder.add(KeyboardButton(text="🏥 На себя"))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True) 