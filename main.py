import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from utils.helpers import is_admin, is_superadmin

# Импорты из ваших модулей
from bot_state import BotState
from config import CONFIG
from handlers import (
    start_help,
    alarm_handlers,
    screenshot,
    manage_handlers,
)
from handlers.current_events import router as current_events_router
from handlers.manage_handlers import check_reminders
print('main.py запускается')
# --- Настройка логирования ---
logger = logging.getLogger(__name__)

def setup_logging():
    # Формат логов
    log_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

    # Логирование в файл
    file_handler = logging.FileHandler("bot.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Логирование в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Основная настройка логгера
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[file_handler, console_handler]
    )

setup_logging()  # Вызываем настройку логирования до всего
logger = logging.getLogger(__name__)


# Глобальные переменные
bot_state = BotState()

# Проверка наличия токена
if "TELEGRAM" not in CONFIG or "TOKEN" not in CONFIG["TELEGRAM"]:
    logger.critical("❌ Токен Telegram не найден в конфиге")
    sys.exit(1)


async def main():
    logger.info("🚀 Запуск бота...")

    # Проверка дублирования запуска (только на Unix)
    lock_file = "/tmp/bot.lock"
    try:
        import fcntl
        global lock_fd
        lock_fd = open(lock_file, 'w')
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError):
            logger.critical("❌ Бот уже запущен!")
            sys.exit(1)
    except ImportError:
        logger.warning("⚠️ Не удалось проверить дублирование запуска — возможно, это Windows")

    # Инициализация бота и диспетчера
    bot = Bot(token=CONFIG["TELEGRAM"]["TOKEN"], default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    await bot_state.load_state()
    logger.info("📂 Состояние загружено")

    # Регистрация роутеров
    dp.include_router(start_help.router)
    dp.include_router(alarm_handlers.router)
    dp.include_router(screenshot.router)
    dp.include_router(manage_handlers.router)
    dp.include_router(current_events_router)

    # Установка команд
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="view", description="Посмотреть JIRA/Confluence"),
        BotCommand(command="new_message", description="Создать сообщение"),
        BotCommand(command="manage", description="Управление событиями"),
        BotCommand(command="alarm_list", description="Список активных событий"),
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Команды установлены")

    # Запуск бота
    try:
        logger.info("🤖 Бот начал работу")
        asyncio.create_task(check_reminders(bot))
        await dp.start_polling(bot)
    finally:
        logger.info("🛑 Бот остановлен")
        await bot_state.save_state()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Бот остановлен пользователем")