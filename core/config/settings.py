import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseSettings:
    """Настройки базы данных"""
    path: str = "data/database.db"
    
@dataclass
class BotSettings:
    """Настройки бота"""
    token: str
    admin_ids: list[int]
    
@dataclass
class Settings:
    """Основные настройки приложения"""
    database: DatabaseSettings
    bot: BotSettings
    
    @classmethod
    def from_env(cls) -> 'Settings':
        """Создать настройки из переменных окружения"""
        return cls(
            database=DatabaseSettings(
                path=os.getenv('DATABASE_PATH', 'data/database.db')
            ),
            bot=BotSettings(
                token=os.getenv('BOT_TOKEN', ''),
                admin_ids=[int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
            )
        ) 