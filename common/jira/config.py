from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from pathlib import Path
import os
from dotenv import load_dotenv

# Явно загружаем .env из корня проекта
dotenv_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

class JiraConfig(BaseSettings):
    """Конфигурация для работы с JIRA."""
    
    # Основные настройки
    JIRA_URL: str = Field(..., description="URL вашего инстанса JIRA")
    JIRA_API_TOKEN: str = Field(..., description="API токен для доступа к JIRA (используется как Bearer token)")
    JIRA_DEFAULT_PROJECT: str = Field(..., description="Ключ проекта по умолчанию")
    
    # Настройки API
    API_VERSION: str = Field(default="2", description="Версия JIRA API")
    REQUEST_TIMEOUT: int = Field(default=30, description="Таймаут запросов в секундах")
    MAX_RETRIES: int = Field(default=3, description="Максимальное количество попыток при ошибке")
    CACHE_TTL: int = Field(default=300, description="Время жизни кэша в секундах")
    
    # Настройки прокси (опционально)
    PROXY_URL: Optional[str] = Field(default=None, description="URL прокси-сервера")
    PROXY_USERNAME: Optional[str] = Field(default=None, description="Имя пользователя прокси")
    PROXY_PASSWORD: Optional[str] = Field(default=None, description="Пароль прокси")
    
    model_config = SettingsConfigDict(
        env_file=str(dotenv_path),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra='ignore'
    ) 