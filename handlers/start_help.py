# handlers/start_help.py
#    📸 < b > JIRA / Confluence < / b > — получить скриншот(календаря работ, jira, confluence)

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards import create_main_keyboard, create_cancel_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder


router = Router()


@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "👋 Привет! Я бот для управления событиями и уведомлениями.\nВыберите действие:",
        reply_markup=create_main_keyboard()
    )


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    help_text = """
📌 <b>Доступные команды:</b>
📢 <b>Сообщить</b> — создать новое сообщение (сбой, работа, обычное)
🛂 <b>Управлять</b> — продление или остановка (сбой, работа)
📕 <b>Текущие события</b> — посмотреть список текущих сбоев и работ
ℹ️ <b>Помощь</b> — показать это окно
"""
    # Убираем комментарий про JIRA/Confluence, если он не нужен
    # Если нужно — можно вернуть

    await message.answer(help_text, reply_markup=create_main_keyboard(), parse_mode='HTML')


# --- Инлайновый обработчик глобальной отмены ---
@router.callback_query(F.data == "cancel_action")
async def handle_global_cancel(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    await callback.message.edit_text("🚫 Действие отменено", reply_markup=None)
    await callback.message.answer("Выберите действие:", reply_markup=create_main_keyboard())
    await callback.answer()