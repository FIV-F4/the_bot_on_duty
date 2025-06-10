"""
Клавиатуры для бота контакт-центра.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def create_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает главную клавиатуру с двумя кнопками.
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками
    """
    keyboard = [
        [KeyboardButton(text="Тех. неполадка")],
        [KeyboardButton(text="Больничный")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите тип заявки"
    ) 