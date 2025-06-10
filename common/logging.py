"""
Общие настройки логирования для всех ботов.
"""
import logging
import os
from pathlib import Path

def setup_logging(bot_name: str) -> logging.Logger:
    """
    Настройка логирования для бота.
    
    Args:
        bot_name: Имя бота для имени лог-файла
        
    Returns:
        Logger: Настроенный логгер
    """
    # Формат логов
    log_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    
    # Создаем директорию для логов, если её нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Логирование в файл
    log_file = log_dir / f"{bot_name}.log"
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
    
    # Создаем и возвращаем логгер для бота
    logger = logging.getLogger(bot_name)
    return logger 