"""
Основной модуль Telegram бота
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from utils.config import CONFIG
from utils.logger import setup_logging
from modules.telegram.states import FAStates
from modules.telegram.keyboards import (
    get_main_keyboard,
    get_keyboard_from_list,
    PROBLEM_LEVELS,
    PROBLEM_SERVICES,
    NAUMEN_FAILURE_TYPES,
    STREAM_1C_OPTIONS,
    INFLUENCE_OPTIONS
)
from modules.jira.client import create_failure_issue

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Проверка наличия токена
if "TELEGRAM" not in CONFIG or "TOKEN" not in CONFIG["TELEGRAM"]:
    logger.critical("❌ Токен Telegram не найден в конфиге")
    sys.exit(1)

# Инициализация бота и диспетчера
bot = Bot(
    token=CONFIG["TELEGRAM"]["TOKEN"],
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Обработчики
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! Я бот для создания задач FA.\n"
        "Нажмите кнопку 'Создать задачу FA' чтобы начать.",
        reply_markup=get_main_keyboard()
    )

@dp.message(lambda message: message.text == "🚨 Создать задачу FA")
async def create_fa_task(message: types.Message, state: FSMContext):
    """Обработчик создания задачи FA"""
    await state.set_state(FAStates.waiting_for_summary)
    await message.answer(
        "Введите краткое описание проблемы (заголовок задачи):",
        reply_markup=ReplyKeyboardRemove()
    )

# ... остальные обработчики ...

async def main():
    """Основная функция запуска бота"""
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 