from datetime import datetime, timedelta
from typing import List, Optional

from domain.entities.failure import Failure, FailureStatus
from domain.interfaces.failure_repository import FailureRepository
from application.services.notification_service import NotificationService

class FailureService:
    """Сервис для работы со сбоями"""
    
    def __init__(
        self,
        failure_repository: FailureRepository,
        notification_service: NotificationService
    ):
        self.repository = failure_repository
        self.notifications = notification_service
    
    async def create_failure(
        self,
        title: str,
        description: str,
        created_by: str
    ) -> Failure:
        """Создать новый сбой"""
        failure = Failure(
            title=title,
            description=description,
            created_by=created_by,
            created_at=datetime.now(),
            status=FailureStatus.ACTIVE
        )
        
        # Сохраняем сбой
        await self.repository.create(failure)
        
        # Отправляем уведомления
        await self.notifications.notify_failure_created(failure)
        
        return failure
    
    async def extend_failure(
        self,
        failure_id: int,
        extended_by: str
    ) -> Optional[Failure]:
        """Продлить сбой"""
        failure = await self.repository.get(failure_id)
        if not failure:
            return None
            
        failure.status = FailureStatus.EXTENDED
        failure.extended_by = extended_by
        failure.extended_at = datetime.now()
        
        # Обновляем сбой
        await self.repository.update(failure)
        
        # Отправляем уведомления
        await self.notifications.notify_failure_extended(failure)
        
        return failure
    
    async def resolve_failure(
        self,
        failure_id: int
    ) -> Optional[Failure]:
        """Разрешить сбой"""
        failure = await self.repository.get(failure_id)
        if not failure:
            return None
            
        failure.status = FailureStatus.RESOLVED
        failure.resolved_at = datetime.now()
        
        # Обновляем сбой
        await self.repository.update(failure)
        
        # Отправляем уведомления
        await self.notifications.notify_failure_resolved(failure)
        
        return failure
    
    async def check_failures(self) -> None:
        """Проверить сбои на необходимость продления или разрешения"""
        # Получаем сбои, которые нужно продлить
        needs_extension = await self.repository.get_needs_extension()
        if needs_extension:
            await self.notifications.notify_needs_extension(needs_extension)
        
        # Получаем сбои, которые нужно разрешить
        needs_resolution = await self.repository.get_needs_resolution()
        if needs_resolution:
            await self.notifications.notify_needs_resolution(needs_resolution)
    
    async def get_active_failures(self) -> List[Failure]:
        """Получить активные сбои"""
        return await self.repository.get_active() 