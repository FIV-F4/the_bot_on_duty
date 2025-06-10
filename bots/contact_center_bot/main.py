"""
Бот для создания заявок в контакт-центре.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from common.logging import setup_logging
from common.auth import AUTH_ENABLED
from common.jira.client import JiraApiClient
from common.jira.config import JiraConfig

# Импорты из локальных модулей
from bots.contact_center_bot.handlers import router
from bots.contact_center_bot.keyboards import create_main_keyboard

# Настройка логирования
logger = setup_logging("contact_center_bot")

async def main():
    """Основная функция запуска бота."""
    logger.info("🚀 Запуск бота контакт-центра...")
    
    # Загружаем переменные окружения из .env файла
    load_dotenv()

    # Проверка наличия токена
    token = os.getenv("CONTACT_CENTER_BOT_TOKEN")
    if not token:
        logger.critical("❌ Токен бота не найден в переменных окружения")
        return
    
    # Инициализация бота и диспетчера
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация роутера
    dp.include_router(router)
    
    # Установка команд
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Команды установлены")
    
    # Запуск бота
    try:
        logger.info("🤖 Бот начал работу")
        await dp.start_polling(bot)
    finally:
        logger.info("🛑 Бот остановлен")
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Бот остановлен пользователем") 