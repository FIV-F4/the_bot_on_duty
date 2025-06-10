from typing import List
from datetime import datetime

from domain.entities.failure import Failure
from infrastructure.telegram.telegram_client import TelegramClient

class NotificationService:
    """Сервис для работы с уведомлениями"""
    
    def __init__(self, telegram_client: TelegramClient):
        self.telegram = telegram_client
    
    async def notify_failure_created(self, failure: Failure) -> None:
        """Уведомить о создании сбоя"""
        # Отправляем уведомление в канал доступности
        await self.telegram.send_message(
            chat_id=self.telegram.availability_channel_id,
            text=(
                f"🚨 Создан новый сбой!\n\n"
                f"Заголовок: {failure.title}\n"
                f"Описание: {failure.description}\n"
                f"Создан: {failure.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
        )
        
        # Создаем тему в канале устранения сбоев
        thread_id = await self.telegram.create_thread(
            chat_id=self.telegram.resolution_channel_id,
            title=f"Сбой: {failure.title}",
            text=(
                f"Создан новый сбой\n\n"
                f"Заголовок: {failure.title}\n"
                f"Описание: {failure.description}\n"
                f"Создан: {failure.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"Создал: {failure.created_by}"
            )
        )
        
        # Обновляем ID темы в сбое
        failure.telegram_thread_id = thread_id
    
    async def notify_failure_extended(self, failure: Failure) -> None:
        """Уведомить о продлении сбоя"""
        if not failure.telegram_thread_id:
            return
            
        await self.telegram.send_message(
            chat_id=self.telegram.resolution_channel_id,
            thread_id=failure.telegram_thread_id,
            text=(
                f"⏳ Сбой продлен\n\n"
                f"Продлен: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"Продлил: {failure.extended_by}"
            )
        )
    
    async def notify_failure_resolved(self, failure: Failure) -> None:
        """Уведомить о разрешении сбоя"""
        if not failure.telegram_thread_id:
            return
            
        await self.telegram.send_message(
            chat_id=self.telegram.resolution_channel_id,
            thread_id=failure.telegram_thread_id,
            text=(
                f"✅ Сбой разрешен\n\n"
                f"Разрешен: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        )
        
        # Уведомляем в канал доступности
        await self.telegram.send_message(
            chat_id=self.telegram.availability_channel_id,
            text=(
                f"✅ Сбой разрешен!\n\n"
                f"Заголовок: {failure.title}\n"
                f"Разрешен: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        )
    
    async def notify_needs_extension(self, failures: List[Failure]) -> None:
        """Уведомить о сбоях, которые нужно продлить"""
        for failure in failures:
            if not failure.telegram_thread_id:
                continue
                
            await self.telegram.send_message(
                chat_id=self.telegram.resolution_channel_id,
                thread_id=failure.telegram_thread_id,
                text=(
                    f"⚠️ Внимание! Сбой нужно продлить\n\n"
                    f"Сбой активен более 24 часов\n"
                    f"Создан: {failure.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
            )
    
    async def notify_needs_resolution(self, failures: List[Failure]) -> None:
        """Уведомить о сбоях, которые нужно разрешить"""
        for failure in failures:
            if not failure.telegram_thread_id:
                continue
                
            await self.telegram.send_message(
                chat_id=self.telegram.resolution_channel_id,
                thread_id=failure.telegram_thread_id,
                text=(
                    f"⚠️ Внимание! Сбой нужно разрешить\n\n"
                    f"Сбой активен более 48 часов\n"
                    f"Создан: {failure.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
            ) 