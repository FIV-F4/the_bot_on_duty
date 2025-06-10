from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from domain.entities.failure import Failure, FailureStatus

class FailureRepository(ABC):
    """Интерфейс репозитория сбоев"""
    
    @abstractmethod
    async def create(self, failure: Failure) -> Failure:
        """Создать новый сбой"""
        pass
    
    @abstractmethod
    async def get(self, failure_id: int) -> Optional[Failure]:
        """Получить сбой по ID"""
        pass
    
    @abstractmethod
    async def get_active(self) -> List[Failure]:
        """Получить все активные сбои"""
        pass
    
    @abstractmethod
    async def update(self, failure: Failure) -> Failure:
        """Обновить сбой"""
        pass
    
    @abstractmethod
    async def update_status(self, failure_id: int, status: FailureStatus) -> Optional[Failure]:
        """Обновить статус сбоя"""
        pass
    
    @abstractmethod
    async def get_needs_extension(self) -> List[Failure]:
        """Получить сбои, которые нужно продлить"""
        pass
    
    @abstractmethod
    async def get_needs_resolution(self) -> List[Failure]:
        """Получить сбои, которые нужно разрешить"""
        pass 