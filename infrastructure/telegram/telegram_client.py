from typing import Optional
import logging
from aiogram import Bot
from aiogram.types import Message

class TelegramClient:
    """Клиент для работы с Telegram"""
    
    def __init__(
        self,
        bot: Bot,
        availability_channel_id: int,
        resolution_channel_id: int
    ):
        self.bot = bot
        self.availability_channel_id = availability_channel_id
        self.resolution_channel_id = resolution_channel_id
        self.logger = logging.getLogger(__name__)
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        thread_id: Optional[int] = None
    ) -> Message:
        """Отправить сообщение"""
        try:
            return await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                message_thread_id=thread_id
            )
        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения: {e}")
            raise
    
    async def create_thread(
        self,
        chat_id: int,
        title: str,
        text: str
    ) -> int:
        """Создать тему и отправить в нее сообщение"""
        try:
            # Отправляем сообщение
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text
            )
            
            # Создаем тему
            thread = await self.bot.create_forum_topic(
                chat_id=chat_id,
                name=title
            )
            
            # Перемещаем сообщение в тему
            await self.bot.move_message(
                chat_id=chat_id,
                message_id=message.message_id,
                from_chat_id=chat_id,
                to_chat_id=chat_id,
                message_thread_id=thread.message_thread_id
            )
            
            return thread.message_thread_id
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании темы: {e}")
            raise 