from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')

class Repository(Generic[T], ABC):
    """Базовый интерфейс репозитория"""
    
    @abstractmethod
    async def get(self, id: int) -> Optional[T]:
        """Получить сущность по ID"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[T]:
        """Получить все сущности"""
        pass
    
    @abstractmethod
    async def add(self, entity: T) -> T:
        """Добавить сущность"""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Обновить сущность"""
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Удалить сущность по ID"""
        pass 