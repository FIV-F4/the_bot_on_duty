# utils.py

from datetime import datetime, timedelta
import re
from typing import Optional

def parse_duration(duration_str: str) -> Optional[timedelta]:
    duration_str = duration_str.lower().strip()
    pattern = r'(\d+)\s*(минут?|мин|час|день)'
    match = re.search(pattern, duration_str)
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    if 'минут' in unit or 'мин' in unit:
        return timedelta(minutes=value)
    elif 'час' in unit:
        return timedelta(hours=value)
    elif 'день' in unit:
        return timedelta(days=value)
    return None

async def get_user_name(user_id: int) -> str:
    from aiogram import Bot
    from config import CONFIG
    bot = Bot(token=CONFIG["TELEGRAM"]["TOKEN"])
    try:
        user = await bot.get_chat_member(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], user_id)
        if user.user.username:
            return f"@{user.user.username}"
        return f"[ID:{user_id}]"
    except Exception:
        return f"[ID:{user_id}]"