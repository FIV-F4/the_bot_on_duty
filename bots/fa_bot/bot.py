from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from core.config.settings import Settings
from core.utils.logger import get_logger
from application.services.user_service import UserService
from application.services.bot_state_service import BotStateService

logger = get_logger(__name__)

class FABot:
    """Базовый класс бота"""
    
    def __init__(self, settings: Settings, user_service: UserService):
        self.settings = settings
        self.user_service = user_service
        self.state_service = BotStateService()
        
        # Инициализация бота и диспетчера
        self.bot = Bot(
            token=settings.bot.token,
            parse_mode=ParseMode.HTML
        )
        self.dp = Dispatcher(storage=MemoryStorage())
        
        # Регистрация обработчиков
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков команд"""
        self.dp.message.register(self.start_handler, Command(commands=["start"]))
        self.dp.message.register(self.help_handler, Command(commands=["help"]))
        # TODO: Добавить остальные обработчики
    
    async def start_handler(self, message: Message):
        """Обработчик команды /start"""
        user = await self.user_service.get_user(message.from_user.id)
        if not user:
            user = await self.user_service.create_user(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            logger.info(f"Создан новый пользователь: {user.user_id}")
        else:
            await self.user_service.update_user_activity(user.user_id)
            logger.info(f"Обновлена активность пользователя: {user.user_id}")
        
        self.state_service.activate_user(user.user_id)
        
        await message.answer(
            f"Привет, {message.from_user.first_name}!\n"
            "Я бот для работы с FA. Используйте /help для получения списка команд."
        )
    
    async def help_handler(self, message: Message):
        """Обработчик команды /help"""
        await message.answer(
            "Доступные команды:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать это сообщение\n"
            # TODO: Добавить остальные команды
        )
    
    async def start(self):
        """Запуск бота"""
        logger.info("Запуск бота...")
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {str(e)}")
            raise 