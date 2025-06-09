from typing import Optional
from datetime import datetime, timedelta

from domain.entities.bot_state import BotState

class BotStateService:
    """Сервис для работы с состоянием бота"""
    
    def __init__(self):
        self._state = BotState()
    
    def activate_user(self, user_id: int) -> None:
        """Активировать пользователя"""
        self._state.add_active_user(user_id)
    
    def deactivate_user(self, user_id: int) -> None:
        """Деактивировать пользователя"""
        self._state.remove_active_user(user_id)
    
    def is_user_active(self, user_id: int) -> bool:
        """Проверить, активен ли пользователь"""
        return self._state.is_user_active(user_id)
    
    def register_admin_command(self, command: str) -> None:
        """Зарегистрировать команду администратора"""
        self._state.add_admin_command(command)
    
    def can_execute_admin_command(self, command: str, cooldown_seconds: int = 300) -> bool:
        """Проверить, можно ли выполнить команду администратора"""
        last_time = self._state.get_admin_command_time(command)
        if not last_time:
            return True
        return datetime.now() - last_time > timedelta(seconds=cooldown_seconds)
    
    def update_screenshot_time(self) -> None:
        """Обновить время последнего скриншота"""
        self._state.set_screenshot_time()
    
    def can_take_screenshot(self, cooldown_seconds: int = 60) -> bool:
        """Проверить, можно ли сделать скриншот"""
        last_time = self._state.get_screenshot_time()
        if not last_time:
            return True
        return datetime.now() - last_time > timedelta(seconds=cooldown_seconds)
    
    def activate_alarm(self) -> None:
        """Активировать тревогу"""
        self._state.activate_alarm()
    
    def deactivate_alarm(self) -> None:
        """Деактивировать тревогу"""
        self._state.deactivate_alarm()
    
    def is_alarm_active(self) -> bool:
        """Проверить, активна ли тревога"""
        return self._state.is_alarm_active
    
    def get_alarm_duration(self) -> Optional[float]:
        """Получить длительность тревоги в секундах"""
        return self._state.get_alarm_duration() 