from typing import Any, Dict, Optional
from pydantic import BaseSettings, Field
from functools import lru_cache


class BaseConfig(BaseSettings):
    """Базовый класс конфигурации."""
    
    # Общие настройки
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    
    # Общие URL
    JIRA_URL: str = Field(..., env="JIRA_URL")
    CONFLUENCE_URL: str = Field(..., env="CONFLUENCE_URL")
    
    # Общие настройки базы данных
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_USER: str = Field(..., env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")
    DB_NAME: str = Field(..., env="DB_NAME")
    
    # Общие настройки Redis
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Общие настройки безопасности
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALLOWED_HOSTS: list[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @classmethod
    @lru_cache()
    def get_settings(cls) -> "BaseConfig":
        """Получение настроек с кэшированием."""
        return cls()

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        """Получение словаря настроек."""
        return super().dict(**kwargs) 