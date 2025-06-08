# utils/helpers.py
from aiogram import Bot
from config import CONFIG
from datetime import datetime, timedelta
import re
from typing import Optional
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types import User

class NewMessageStates(StatesGroup):
    SELECTING_TYPE = State()
    ENTER_DESCRIPTION = State()
    ENTER_FIX_TIME = State()
    ENTER_START_TIME = State()
    ENTER_END_TIME = State()
    ENTER_UNAVAILABLE_SERVICES = State()
    ENTER_MESSAGE_TEXT = State()
    CONFIRMATION = State()


def parse_duration(duration_str: str) -> Optional[timedelta]:
    duration_str = duration_str.lower().strip()

    # Поддержка форматов: "через 1 час", "1 час", "30 мин", "через 2 дня"
    pattern = r'(\d+[\.,]?\d*)\s*(минут?|час|день)'
    match = re.search(pattern, duration_str)

    if not match:
        return None

    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)

    if 'минут' in unit or 'мин' in unit:
        return timedelta(minutes=value)
    elif 'час' in unit:
        return timedelta(hours=value)
    elif 'день' in unit:
        return timedelta(days=value)

    return None


async def get_user_name(user_id: int, bot: Bot) -> str:
    try:
        user = await bot.get_chat_member(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], user_id)
        if user.user.username:
            return f"@{user.user.username}"
        return f"[ID:{user_id}]"
    except Exception:
        return f"[ID:{user_id}]"


def is_admin(user_id: int) -> bool:
    from config import CONFIG
    return user_id in CONFIG.get("TELEGRAM", {}).get("ADMIN_IDS", [])


def is_superadmin(user_id: int) -> bool:
    from config import CONFIG
    return user_id in CONFIG.get("TELEGRAM", {}).get("SUPERADMIN_IDS", [])