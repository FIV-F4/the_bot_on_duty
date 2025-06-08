# bot_state.py

import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from threading import RLock
from collections import deque
import logging
from aiogram.fsm.state import State
from config import CONFIG

logger = logging.getLogger(__name__)
STATE_FILE = "data/state.json"
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)


def safe_parse_time(time_str: str) -> Optional[datetime]:
    """
    Безопасный парсер времени из строки.
    Возвращает None, если формат некорректен.
    """
    if not time_str:
        return None
    try:
        # Если уже datetime — возвращаем как есть
        if isinstance(time_str, datetime):
            return time_str
        # Иначе пробуем разобрать как ISO-строку
        return datetime.fromisoformat(time_str)
    except Exception as e:
        logger.warning(f"⚠️ Невозможно разобрать время: {time_str} ({e})")
        return None


class BotState:
    def __init__(self):
        logger.info("🔧 Инициализация BotState")
        self.active_alarms: Dict[str, Dict] = {}
        self.user_states: Dict[int, Dict] = {}
        self._lock = RLock()
        self.extension_queue: Dict[int, deque] = {}  # {user_id: deque(alarm_ids)}
        self.user_processing: set = set()
        self.active_maintenances: Dict[str, Dict] = {}

    def get_user_active_alarms(self, user_id: int) -> dict:
        return {
            aid: alarm for aid, alarm in self.active_alarms.items()
            if alarm["user_id"] == user_id
        }

    def get_user_active_maintenances(self, user_id: int) -> dict:
        return {
            wid: work for wid, work in self.active_maintenances.items()
            if work["user_id"] == user_id or user_id in CONFIG["TELEGRAM"].get("SUPERADMIN_IDS", [])
        }

    def _save_to_file(self, state: dict):
        """Метод сохранения в файл с использованием контекстного менеджера"""
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    async def save_state(self):
        """Сохраняет текущее состояние бота в файл"""
        logger.info("💾 Начинаю сохранение состояния бота")

        state = {
            'active_alarms': {},
            'active_maintenances': {},
            'user_states': {}
        }

        with self._lock:
            # --- Сохранение аварий ---
            for alarm_id, alarm in self.active_alarms.items():
                logger.debug(f"💾 Сохраняю аварию: {alarm_id}")
                fix_time = alarm['fix_time']
                created_at = alarm.get('created_at')

                # Проверяем тип перед isoformat
                state['active_alarms'][alarm_id] = {
                    'issue': alarm['issue'],
                    'fix_time': fix_time.isoformat() if isinstance(fix_time, datetime) else fix_time,
                    'user_id': alarm['user_id'],
                    'created_at': created_at.isoformat() if isinstance(created_at, datetime) else created_at
                }

            # --- Сохранение регламентных работ ---
            for work_id, work in self.active_maintenances.items():
                logger.debug(f"💾 Сохраняю работу: {work_id}")
                start_time = work['start_time']
                end_time = work['end_time']
                created_at = work['created_at']

                state['active_maintenances'][work_id] = {
                    'description': work['description'],
                    'start_time': start_time.isoformat() if isinstance(start_time, datetime) else start_time,
                    'end_time': end_time.isoformat() if isinstance(end_time, datetime) else end_time,
                    'unavailable_services': work.get('unavailable_services', 'не указано'),
                    'user_id': work.get('user_id'),
                    'created_at': created_at.isoformat() if isinstance(created_at, datetime) else created_at
                }

            # --- Сохранение пользовательских состояний ---
            for user_id, user_state in self.user_states.items():
                logger.debug(f"💾 Сохраняю состояние пользователя: {user_id}")
                state['user_states'][str(user_id)] = {
                    'state': user_state['state'].name if isinstance(user_state['state'], State) else user_state['state'],
                    'alarm_id': user_state.get('alarm_id'),
                    'issue': user_state.get('issue')
                }

        try:
            await asyncio.to_thread(self._save_to_file, state)
            logger.info("✅ Состояние успешно сохранено")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения состояния: {str(e)}", exc_info=True)

    async def load_state(self):
        """Загружает состояние бота из файла"""
        logger.info("📂 Загружаю состояние из файла...")
        try:
            data = await asyncio.to_thread(json.load, open(STATE_FILE, "r", encoding="utf-8"))
            logger.info("✅ Файл состояния загружен")
            with self._lock:
                self.active_alarms.clear()
                self.active_maintenances.clear()
                self.user_states.clear()

            # --- Загрузка аварий ---
            for alarm_id, alarm_data in data.get("active_alarms", {}).items():
                fix_time = safe_parse_time(alarm_data.get("fix_time"))
                created_at = safe_parse_time(alarm_data.get("created_at"))

                if not all([fix_time, created_at]):
                    continue

                self.active_alarms[alarm_id] = {
                    "issue": alarm_data["issue"],
                    "fix_time": fix_time,
                    "user_id": alarm_data["user_id"],
                    "created_at": created_at
                }
                logger.debug(f"📥 Восстановлена авария: {alarm_id}")

            # --- Загрузка регламентных работ ---
            for work_id, work_data in data.get("active_maintenances", {}).items():
                start_time = safe_parse_time(work_data.get("start_time"))
                end_time = safe_parse_time(work_data.get("end_time"))
                created_at = safe_parse_time(work_data.get("created_at"))

                if not all([start_time, end_time, created_at]):
                    continue

                self.active_maintenances[work_id] = {
                    "description": work_data["description"],
                    "start_time": start_time,
                    "end_time": end_time,
                    "user_id": work_data["user_id"],
                    "created_at": created_at,
                    "unavailable_services": work_data.get("unavailable_services", "не указано")
                }
                logger.debug(f"📥 Восстановлена работа: {work_id}")

            # --- Загрузка пользовательских состояний ---
            for user_id_str, user_state in data.get("user_states", {}).items():
                try:
                    user_id = int(user_id_str)
                    state_name = user_state.get('state')
                    alarm_id = user_state.get('alarm_id')
                    issue = user_state.get('issue')

                    if not state_name:
                        continue

                    self.user_states[user_id] = {
                        'state': state_name,
                        'alarm_id': alarm_id,
                        'issue': issue
                    }
                except ValueError as ve:
                    logger.warning(f"⚠️ Ошибка при обработке состояния пользователя {user_id_str}: {ve}")
                except Exception as e:
                    logger.error(f"❌ Неожиданная ошибка: {e}", exc_info=True)

        except FileNotFoundError:
            logger.info("🆕 Файл состояния не найден. Создание нового состояния")
        except json.JSONDecodeError as je:
            logger.warning(f"⚠️ Не удалось распарсить файл состояния: {je}")
            logger.info("🔄 Создаю новое состояние вместо повреждённого")
        except Exception as e:
            logger.critical(f"❌ Критическая ошибка при загрузке состояния: {str(e)}", exc_info=True)

# --- Глобальное состояние бота ---
bot_state = BotState()