"""
Конфигурация приложения
"""
import json
import os
from typing import Dict, Any

# Путь к файлу конфигурации
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")

def load_config() -> Dict[str, Any]:
    """
    Загружает конфигурацию из файла
    
    Returns:
        Dict[str, Any]: Конфигурация приложения
    """
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Ошибка загрузки конфигурации: {str(e)}")

# Загружаем конфигурацию
CONFIG = load_config() 