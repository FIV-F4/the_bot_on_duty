import logging
import os
from datetime import datetime

def setup_logging(log_dir: str = "logs") -> None:
    """Настройка логирования"""
    # Создаем директорию для логов, если её нет
    os.makedirs(log_dir, exist_ok=True)
    
    # Формат логов
    log_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    
    # Имя файла лога с датой
    log_file = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Логирование в файл
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Логирование в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Основная настройка логгера
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[file_handler, console_handler]
    )
    
    # Отключаем лишние логи от сторонних библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Получить логгер с указанным именем"""
    return logging.getLogger(name) 