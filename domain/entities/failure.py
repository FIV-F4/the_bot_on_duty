from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class FailureStatus(Enum):
    """Статус сбоя"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    EXTENDED = "extended"

@dataclass
class Failure:
    """Сущность сбоя"""
    id: int
    title: str
    description: str
    created_by: int  # ID пользователя, создавшего сбой
    created_at: datetime
    status: FailureStatus
    telegram_thread_id: Optional[int] = None  # ID темы в Telegram
    resolved_at: Optional[datetime] = None
    extended_at: Optional[datetime] = None
    extended_by: Optional[int] = None  # ID пользователя, продлившего сбой
    
    def is_active(self) -> bool:
        """Проверяет, активен ли сбой"""
        return self.status == FailureStatus.ACTIVE
    
    def is_extended(self) -> bool:
        """Проверяет, продлен ли сбой"""
        return self.status == FailureStatus.EXTENDED
    
    def is_resolved(self) -> bool:
        """Проверяет, разрешен ли сбой"""
        return self.status == FailureStatus.RESOLVED
    
    def needs_extension(self) -> bool:
        """Проверяет, нужно ли продлить сбой"""
        if not self.is_active():
            return False
        # Если сбой активен более 24 часов, его нужно продлить
        return (datetime.now() - self.created_at).total_seconds() > 86400
    
    def needs_resolution(self) -> bool:
        """Проверяет, нужно ли разрешить сбой"""
        if not self.is_active():
            return False
        # Если сбой активен более 48 часов, его нужно разрешить
        return (datetime.now() - self.created_at).total_seconds() > 172800 