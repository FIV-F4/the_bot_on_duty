import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class EnvLoader:
    """Загрузчик переменных окружения."""
    
    @staticmethod
    def load_env(env_file: Optional[str] = None) -> None:
        """
        Загрузка переменных окружения из файла.
        
        Args:
            env_file: Путь к файлу .env. Если не указан, ищется в корне проекта.
        """
        if env_file is None:
            # Поиск .env файла в корне проекта
            root_dir = Path(__file__).parent.parent.parent
            env_file = root_dir / ".env"
            
            if not env_file.exists():
                # Если не найден в корне, ищем в текущей директории
                env_file = Path.cwd() / ".env"
        
        if env_file.exists():
            load_dotenv(env_file)
        else:
            raise FileNotFoundError(f"Файл .env не найден: {env_file}")
    
    @staticmethod
    def get_env(key: str, default: Optional[str] = None) -> str:
        """
        Получение значения переменной окружения.
        
        Args:
            key: Ключ переменной окружения
            default: Значение по умолчанию
            
        Returns:
            Значение переменной окружения
            
        Raises:
            KeyError: Если переменная не найдена и не указано значение по умолчанию
        """
        value = os.getenv(key, default)
        if value is None:
            raise KeyError(f"Переменная окружения {key} не найдена")
        return value 