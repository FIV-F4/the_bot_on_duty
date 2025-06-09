import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from application.handlers.failure_handlers import router as failure_router
from application.services.failure_service import FailureService
from application.services.notification_service import NotificationService
from infrastructure.repositories.failure_repository import FileFailureRepository
from infrastructure.telegram.telegram_client import TelegramClient

class FailureBot:
    """Бот для работы со сбоями"""
    
    def __init__(
        self,
        token: str,
        availability_channel_id: int,
        resolution_channel_id: int,
        failures_file: str
    ):
        self.bot = Bot(token=token)
        self.dp = Dispatcher(storage=MemoryStorage())
        
        # Инициализируем зависимости
        self.telegram_client = TelegramClient(
            bot=self.bot,
            availability_channel_id=availability_channel_id,
            resolution_channel_id=resolution_channel_id
        )
        
        self.failure_repository = FileFailureRepository(failures_file)
        self.notification_service = NotificationService(self.telegram_client)
        self.failure_service = FailureService(
            self.failure_repository,
            self.notification_service
        )
        
        # Регистрируем роутеры
        self.dp.include_router(failure_router)
        
        # Внедряем зависимости
        self.dp["failure_service"] = self.failure_service
        
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Запустить бота"""
        try:
            # Запускаем проверку сбоев
            asyncio.create_task(self._check_failures())
            
            # Запускаем бота
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            self.logger.error(f"Ошибка при запуске бота: {e}")
            raise
    
    async def _check_failures(self):
        """Периодическая проверка сбоев"""
        while True:
            try:
                await self.failure_service.check_failures()
            except Exception as e:
                self.logger.error(f"Ошибка при проверке сбоев: {e}")
            
            # Проверяем каждые 5 минут
            await asyncio.sleep(300)
    
    async def stop(self):
        """Остановить бота"""
        await self.bot.session.close() 