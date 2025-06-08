import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User
from handlers.alarm_handlers import new_message_2fa

@pytest.mark.asyncio
async def test_new_message_2fa():
    # Создаем мок-объекты
    message = MagicMock(spec=Message)
    message.text = "🚨 Сбой+FA"
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.answer = AsyncMock()
    
    # Вызываем обработчик
    await new_message_2fa(message)
    
    # Проверяем, что бот ответил правильным текстом
    message.answer.assert_called_once()
    call_args = message.answer.call_args[1]
    assert "Опишите проблему" in call_args['text']
    assert call_args['reply_markup'] is not None 