# handlers/start_help.py

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards import create_main_keyboard

router = Router()

@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer("👋 Привет! Я бот для управления событиями и уведомлениями.\nВыберите действие:", reply_markup=create_main_keyboard())

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    help_text = """
📌 <b>Доступные команды:</b>
📸 <b>JIRA/Confluence</b> — получить скриншот (календаря работ, jira, confluence)
📢 <b>Сообщить</b> — создать новое сообщение (сбой, работа, обычное)
🔄 <b>Продлить</b> — продлить время сбоя или регламентной работы
🛑 <b>Остановить сбой</b> — завершить активный сбой
📕 <b>Текущие события</b> — посмотреть список текущих сбоев и работ
ℹ️ <b>Помощь</b> — показать это окно
"""
    await message.answer(help_text, reply_markup=create_main_keyboard(), parse_mode='HTML')

# --- Обработчик глобальной отмены ---
@router.message(F.text == "❌ Отмена")
async def handle_global_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    await message.answer("🚫 Действие отменено", reply_markup=create_main_keyboard())