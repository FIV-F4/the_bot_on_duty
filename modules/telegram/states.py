"""
Состояния FSM для Telegram бота
"""
from aiogram.fsm.state import State, StatesGroup

class FAStates(StatesGroup):
    """Состояния для создания задачи FA"""
    waiting_for_summary = State()
    waiting_for_description = State()
    waiting_for_level = State()
    waiting_for_service = State()
    waiting_for_naumen_type = State()
    waiting_for_stream_1c = State()
    waiting_for_influence = State()
    waiting_for_confirmation = State() 