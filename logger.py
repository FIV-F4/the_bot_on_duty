# logger.py

import logging
import os
from logging.handlers import RotatingFileHandler
from aiogram import loggers as aiogram_loggers

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

MAX_LOG_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_ERROR_LOG_BYTES = 2 * 1024 * 1024  # 2 MB
LOG_BACKUP_COUNT = 5
ERROR_LOG_BACKUP_COUNT = 3

def setup_logging():
    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Форматтер
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # Логгер для общих событий
    info_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "info.log"),
        maxBytes=MAX_LOG_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    info_handler.setFormatter(formatter)
    info_handler.setLevel(logging.INFO)
    root_logger.addHandler(info_handler)

    # Логгер для ошибок
    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "error.log"),
        maxBytes=MAX_ERROR_LOG_BYTES,
        backupCount=ERROR_LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    # Логгер для Aiogram
    aiogram_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", DATE_FORMAT)
    aiogram_file_handler = logging.FileHandler(os.path.join(LOG_DIR, "aiogram.log"))
    aiogram_file_handler.setFormatter(aiogram_formatter)
    aiogram_loggers.logger.setLevel(logging.INFO)
    aiogram_loggers.logger.addHandler(aiogram_file_handler)

    # Вывод в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)

    return root_logger

logger = setup_logging()