from typing import Optional
from pydantic import Field

from .base_config import BaseConfig


class TelegramConfig(BaseConfig):
    """Конфигурация для Telegram бота."""
    
    # Настройки Telegram
    TELEGRAM_BOT_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_API_ID: int = Field(..., env="TELEGRAM_API_ID")
    TELEGRAM_API_HASH: str = Field(..., env="TELEGRAM_API_HASH")
    
    # Настройки сессии
    SESSION_NAME: str = Field(default="bot_session", env="SESSION_NAME")
    SESSION_STRING: Optional[str] = Field(default=None, env="SESSION_STRING")
    
    # Настройки прокси (опционально)
    PROXY_URL: Optional[str] = Field(default=None, env="PROXY_URL")
    PROXY_USERNAME: Optional[str] = Field(default=None, env="PROXY_USERNAME")
    PROXY_PASSWORD: Optional[str] = Field(default=None, env="PROXY_PASSWORD")
    
    # Настройки администраторов
    ADMIN_IDS: list[int] = Field(default=[], env="ADMIN_IDS")
    SUPERADMIN_IDS: list[int] = Field(default=[], env="SUPERADMIN_IDS")
    
    # Настройки групп
    MAIN_GROUP_ID: int = Field(..., env="MAIN_GROUP_ID")
    LOG_GROUP_ID: Optional[int] = Field(default=None, env="LOG_GROUP_ID")
    
    class Config:
        env_prefix = "TELEGRAM_" 