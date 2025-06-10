"""
Общие настройки аутентификации для всех ботов.
"""
from typing import List, Optional
from functools import wraps
from aiogram.types import Message
import logging

# Константа для включения/отключения проверки прав
AUTH_ENABLED = True

# Список администраторов (можно загружать из конфига)
ADMIN_IDS: List[int] = []
SUPERADMIN_IDS: List[int] = []

logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если пользователь админ или суперадмин
    """
    return user_id in ADMIN_IDS or is_superadmin(user_id)

def is_superadmin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь суперадминистратором.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если пользователь суперадмин
    """
    return user_id in SUPERADMIN_IDS

def admin_required(auth_enabled_for_bot: bool = True):
    """
    Декоратор для проверки прав администратора.
    
    Args:
        auth_enabled_for_bot: Флаг включения/отключения проверки прав для бота
        func: Функция-обработчик
        
    Returns:
        Обертка с проверкой прав
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            if not auth_enabled_for_bot:
                return await func(message, *args, **kwargs)

            if is_admin(message.from_user.id):
                return await func(message, *args, **kwargs)
            else:
                logger.warning(
                    f"Пользователь {message.from_user.id} (@{message.from_user.username}) "
                    f"попытался получить доступ к функции {func.__name__}, но не является администратором."
                )
                await message.answer("У вас нет прав для выполнения этой команды.")
        return wrapper
    return decorator

def superadmin_required(auth_enabled_for_bot: bool = True):
    """
    Декоратор для проверки прав суперадминистратора.
    
    Args:
        auth_enabled_for_bot: Флаг включения/отключения проверки прав для бота
        func: Функция-обработчик
        
    Returns:
        Обертка с проверкой прав
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            if not auth_enabled_for_bot:
                return await func(message, *args, **kwargs)

            if is_superadmin(message.from_user.id):
                return await func(message, *args, **kwargs)
            else:
                logger.warning(
                    f"Пользователь {message.from_user.id} (@{message.from_user.username}) "
                    f"попытался получить доступ к функции {func.__name__}, но не является суперадминистратором."
                )
                await message.answer("У вас нет прав для выполнения этой команды.")
        return wrapper
    return decorator 