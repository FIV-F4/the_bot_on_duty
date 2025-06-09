from dataclasses import dataclass, field
from typing import Dict, Set, Optional
from datetime import datetime

@dataclass
class BotState:
    """Состояние бота"""
    active_users: Set[int] = field(default_factory=set)
    admin_commands: Dict[str, datetime] = field(default_factory=dict)
    last_screenshot_time: Optional[datetime] = None
    is_alarm_active: bool = False
    alarm_start_time: Optional[datetime] = None
    
    def add_active_user(self, user_id: int) -> None:
        """Добавить активного пользователя"""
        self.active_users.add(user_id)
    
    def remove_active_user(self, user_id: int) -> None:
        """Удалить активного пользователя"""
        self.active_users.discard(user_id)
    
    def is_user_active(self, user_id: int) -> bool:
        """Проверить, активен ли пользователь"""
        return user_id in self.active_users
    
    def add_admin_command(self, command: str) -> None:
        """Добавить команду администратора"""
        self.admin_commands[command] = datetime.now()
    
    def get_admin_command_time(self, command: str) -> Optional[datetime]:
        """Получить время выполнения команды администратора"""
        return self.admin_commands.get(command)
    
    def set_screenshot_time(self) -> None:
        """Установить время последнего скриншота"""
        self.last_screenshot_time = datetime.now()
    
    def get_screenshot_time(self) -> Optional[datetime]:
        """Получить время последнего скриншота"""
        return self.last_screenshot_time
    
    def activate_alarm(self) -> None:
        """Активировать тревогу"""
        self.is_alarm_active = True
        self.alarm_start_time = datetime.now()
    
    def deactivate_alarm(self) -> None:
        """Деактивировать тревогу"""
        self.is_alarm_active = False
        self.alarm_start_time = None
    
    def get_alarm_duration(self) -> Optional[float]:
        """Получить длительность тревоги в секундах"""
        if self.is_alarm_active and self.alarm_start_time:
            return (datetime.now() - self.alarm_start_time).total_seconds()
        return None 