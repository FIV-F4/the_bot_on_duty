# manage_handlers.py
import logging
from datetime import datetime, timedelta
import asyncio

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode

from bot_state import bot_state
from keyboards import (
    create_stop_type_keyboard,
    create_action_keyboard,
    create_alarm_selection_keyboard,
    create_maintenance_selection_keyboard,
    create_extension_time_keyboard,
    create_reminder_keyboard
)
from utils.helpers import is_admin, is_superadmin, get_user_name
from config import CONFIG

logger = logging.getLogger(__name__)
router = Router()


# --- Состояния FSM ---
class StopStates(StatesGroup):
    SELECT_TYPE = State()           # Выбор типа (Сбой / Работа)
    SELECT_ACTION = State()         # Остановить / Продлить
    SELECT_ALARM_DURATION = State() # Время продления сбоя
    ENTER_MAINTENANCE_END = State() # Новое время окончания работы
    SELECT_ITEM = State()           # Выбор конкретного события


class ReminderStates(StatesGroup):
    WAITING_FOR_EXTENSION = State()


# --- Команда /manage или кнопка "🛂 Управлять" ---
@router.message(Command("manage"))
@router.message(F.text == "🛂 Управлять")
async def stop_selection(message: Message, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Пользователь начал управление событиями", exc_info=True)

    if not is_admin(user_id):
        logger.warning(f"[{user_id}] Пользователь не является админом — доступ запрещён")
        await message.answer("❌ У вас нет прав для выполнения этой команды", parse_mode=ParseMode.HTML)
        return

    await state.clear()
    logger.info(f"[{user_id}] Очистка состояния завершена")
    await message.answer("Выберите тип события:", reply_markup=create_stop_type_keyboard())
    await state.set_state(StopStates.SELECT_TYPE)
    logger.info(f"[{user_id}] Перешёл в состояние SELECT_TYPE")


# --- Выбор типа события (Сбой / Работа) ---
@router.message(StopStates.SELECT_TYPE)
async def select_event_type(message: Message, state: FSMContext):
    user_id = message.from_user.id
    choice = message.text.strip()
    logger.info(f"[{user_id}] Пользователь выбрал тип события: {choice}")

    if choice == "❌ Отмена":
        logger.info(f"[{user_id}] Действие отменено пользователем")
        await state.clear()
        await message.answer("🚫 Действие отменено", reply_markup=None)
        return

    elif choice == "🚨 Сбой 🚨":
        user_alarms = bot_state.get_user_active_alarms(user_id)
        logger.info(f"[{user_id}] Запрошены активные сбои пользователя")

        if not user_alarms and not is_superadmin(user_id):
            logger.warning(f"[{user_id}] У пользователя нет активных сбоев")
            await message.answer("❌ У вас нет активных сбоев", reply_markup=None)
            return

        keyboard = create_alarm_selection_keyboard(user_alarms)
        await state.update_data(type="alarm")
        logger.info(f"[{user_id}] Показаны доступные сбои")
        await message.answer("Выберите сбой:", reply_markup=keyboard)
        await state.set_state(StopStates.SELECT_ITEM)
        logger.info(f"[{user_id}] Перешёл в состояние SELECT_ITEM")

    elif choice == "🔧 Работа 🔧":
        active_works = bot_state.active_maintenances
        works_by_author = {
            wid: work for wid, work in active_works.items()
            if work["user_id"] == user_id or is_superadmin(user_id)
        }

        if not works_by_author:
            logger.warning(f"[{user_id}] Нет доступных работ")
            await message.answer("❌ У вас нет активных работ", reply_markup=None)
            return

        keyboard = create_maintenance_selection_keyboard(works_by_author)
        await state.update_data(type="maintenance")
        logger.info(f"[{user_id}] Показаны доступные работы")
        await message.answer("Выберите работу:", reply_markup=keyboard)
        await state.set_state(StopStates.SELECT_ITEM)
        logger.info(f"[{user_id}] Перешёл в состояние SELECT_ITEM")

    else:
        logger.warning(f"[{user_id}] Некорректный выбор: {choice}")
        await message.answer("⚠️ Некорректный выбор", reply_markup=create_stop_type_keyboard())


# --- Выбор конкретного события ---
@router.callback_query(lambda call: call.data.startswith("select_"))
async def select_action(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    raw_data = call.data[7:]  # select_alarm_abc123 → alarm_abc123
    logger.info(f"[{user_id}] Получен callback: {call.data}")

    try:
        parts = raw_data.split("_", 1)
        if len(parts) < 2:
            logger.warning(f"[{user_id}] Некорректный callback_data: {call.data}")
            await call.answer("❌ Неверные данные", show_alert=True)
            return

        data_type, item_id = parts
        logger.debug(f"[{user_id}] Тип: {data_type}, ID: {item_id}")

        if data_type == "alarm" and item_id not in bot_state.active_alarms:
            logger.warning(f"[{user_id}] Сбой {item_id} не найден")
            await call.answer("❌ Сбой не найден", show_alert=True)
            return
        elif data_type == "maintenance" and item_id not in bot_state.active_maintenances:
            logger.warning(f"[{user_id}] Работа {item_id} не найдена")
            await call.answer("❌ Работа не найдена", show_alert=True)
            return

        await state.update_data(data_type=data_type, item_id=item_id)
        logger.info(f"[{user_id}] Выбран {data_type}: {item_id}")
        await call.message.edit_text("Выберите действие:", reply_markup=create_action_keyboard())
        await state.set_state(StopStates.SELECT_ACTION)
        logger.info(f"[{user_id}] Перешёл в состояние SELECT_ACTION")

    except Exception as e:
        logger.error(f"[{user_id}] Ошибка при обработке callback: {str(e)}", exc_info=True)
        await call.answer("❌ Не удалось продолжить", show_alert=True)


# --- Обработка действия: Остановить / Продлить ---
@router.callback_query(StopStates.SELECT_ACTION)
async def handle_action_callback(call: CallbackQuery, state: FSMContext):
    action = call.data
    data = await state.get_data()
    data_type = data['data_type']
    item_id = data['item_id']
    logger.info(f"[{call.from_user.id}] Выбрано действие: {action} для {data_type}: {item_id}")

    if action == "action_stop":
        logger.info(f"[{call.from_user.id}] Начата остановка {data_type}: {item_id}")

        if data_type == "alarm":
            alarm_info = bot_state.active_alarms[item_id]
            del bot_state.active_alarms[item_id]
            text = (
                f"✅ <b>Сбой завершён</b>\n"
                f"• <b>Проблема:</b> {alarm_info['issue']}\n"
            )
            await call.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], text, parse_mode="HTML")
            logger.info(f"[{call.from_user.id}] Сбой {item_id} удалён из состояния")

        elif data_type == "maintenance":
            maint_info = bot_state.active_maintenances[item_id]
            del bot_state.active_maintenances[item_id]
            text = (
                f"✅ <b>Работа завершена</b>\n"
                f"• <b>Описание:</b> {maint_info['description']}\n"
            )
            await call.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], text, parse_mode="HTML")
            logger.info(f"[{call.from_user.id}] Работа {item_id} удалена из состояния")

        await call.message.edit_text(f"{('🚨 Сбой' if data_type == 'alarm' else '🔧 Работа')} {item_id} остановлен(а)")
        await bot_state.save_state()
        logger.info(f"[{call.from_user.id}] Бот сохранил обновлённое состояние")
        await state.clear()
        logger.info(f"[{call.from_user.id}] FSM очищена после остановки")

    elif action == "action_extend":
        logger.info(f"[{call.from_user.id}] Начато продление {data_type}: {item_id}")
        if data_type == "alarm":
            await call.message.edit_text("На сколько продлить сбой?", reply_markup=create_extension_time_keyboard())
            await state.set_state(StopStates.SELECT_ALARM_DURATION)
            logger.info(f"[{call.from_user.id}] Перешёл в состояние SELECT_ALARM_DURATION")
        elif data_type == "maintenance":
            await call.message.edit_text("Введите новое время окончания в формате dd.mm.yyyy hh:mm")
            await state.set_state(StopStates.ENTER_MAINTENANCE_END)
            logger.info(f"[{call.from_user.id}] Перешёл в состояние ENTER_MAINTENANCE_END")

    await call.answer()


# --- Продление сбоя на определённое время ---
@router.callback_query(StopStates.SELECT_ALARM_DURATION)
async def handle_alarm_extension_callback(call: CallbackQuery, state: FSMContext):
    duration = call.data
    data = await state.get_data()
    item_id = data['item_id']
    logger.info(f"[{call.from_user.id}] Выбрано продление сбоя {item_id} на {duration}")

    alarm = bot_state.active_alarms.get(item_id)
    if not alarm:
        logger.warning(f"[{call.from_user.id}] Сбой {item_id} не найден")
        await call.message.answer("❌ Сбой не найден")
        await call.answer()
        return

    fix_time_value = alarm.get("fix_time")
    logger.debug(f"[{item_id}] fix_time: {repr(fix_time_value)}, type: {type(fix_time_value)}")

    old_end = None
    if isinstance(fix_time_value, str):
        try:
            old_end = datetime.fromisoformat(fix_time_value)
        except ValueError:
            logger.error(f"[{call.from_user.id}] Неверный формат времени у сбоя {item_id}")
            await call.message.answer("❌ Неверный формат времени")
            await call.answer()
            return
    elif isinstance(fix_time_value, datetime):
        old_end = fix_time_value
    else:
        logger.warning(f"[{call.from_user.id}] Некорректное значение fix_time для сбоя {item_id}")
        await call.message.answer("❌ Некорректное время завершения")
        await call.answer()
        return

    delta = None
    if duration == "extend_30_min":
        delta = timedelta(minutes=30)
        logger.info(f"[{call.from_user.id}] Продление: +30 мин")
    elif duration == "extend_1_hour":
        delta = timedelta(hours=1)
        logger.info(f"[{call.from_user.id}] Продление: +1 час")
    elif duration == "extend_cancel":
        logger.info(f"[{call.from_user.id}] Продление отменено пользователем")
        await state.clear()
        await call.message.edit_text("🚫 Продление отменено")
        await call.answer()
        return
    else:
        logger.warning(f"[{call.from_user.id}] Некорректный выбор: {duration}")
        await call.answer("⚠️ Некорректный выбор", show_alert=True)
        return

    new_end = old_end + delta
    alarm["fix_time"] = new_end.isoformat()
    logger.info(f"[{call.from_user.id}] Новое время завершения: {new_end.isoformat()}")

    text = (
        f"🔄 <b>Сбой продлён</b>\n"
        f"• <b>Проблема:</b> {alarm['issue']}\n"
        f"• <b>Новое время окончания:</b> {new_end.strftime('%d.%m.%Y %H:%M')}\n"
    )

    await call.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], text, parse_mode="HTML")
    logger.info(f"[{call.from_user.id}] Сообщение о продлении отправлено в канал")
    await call.message.edit_text(f"🕒 Сбой {item_id} продлён до {new_end.strftime('%d.%m.%Y %H:%M')}")
    await bot_state.save_state()
    logger.info(f"[{call.from_user.id}] Сохранено обновлённое состояние")
    await state.clear()
    logger.info(f"[{call.from_user.id}] FSM очищена после продления")
    await call.answer()


# --- Продление работы на новое время ---
@router.message(StopStates.ENTER_MAINTENANCE_END)
async def handle_maintenance_new_end(message: Message, state: FSMContext):
    new_time_str = message.text.strip()
    data = await state.get_data()
    item_id = data['item_id']
    logger.info(f"[{message.from_user.id}] Введено новое время: {new_time_str}")

    maint = bot_state.active_maintenances.get(item_id)
    if not maint:
        logger.warning(f"[{message.from_user.id}] Работа {item_id} не найдена")
        await message.answer("❌ Работа не найдена")
        return

    try:
        new_time = datetime.strptime(new_time_str, "%d.%m.%Y %H:%M")
        maint["end"] = new_time.isoformat()
        logger.info(f"[{message.from_user.id}] Новое время установлено: {new_time.isoformat()}")

        text = (
            f"🔄 <b>Работа продлена</b>\n"
            f"• <b>Описание:</b> {maint['description']}\n"
            f"• <b>Новое время окончания:</b> {new_time.strftime('%d.%m.%Y %H:%M')}\n"
        )

        await message.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], text, parse_mode="HTML")
        logger.info(f"[{message.from_user.id}] Сообщение о продлении работы отправлено в канал")
        await message.answer(f"🕒 Работа {item_id} продлена до {new_time.strftime('%d.%m.%Y %H:%M')}")
        await bot_state.save_state()
        logger.info(f"[{message.from_user.id}] Сохранено обновлённое состояние")
        await state.clear()
        logger.info(f"[{message.from_user.id}] FSM очищена после продления")
    except ValueError:
        logger.warning(f"[{message.from_user.id}] Неверный формат даты: {new_time_str}")
        await message.answer("❌ Неверный формат даты. Используйте: dd.mm.yyyy hh:mm")


# --- Фоновая задача: напоминание за 5 минут до конца сбоя ---
async def check_reminders(bot):
    while True:
        now = datetime.now()
        logger.info(f"[REMINDER] Проверка уведомлений. Текущее время: {now.isoformat()}")
        for alarm_id, alarm in bot_state.active_alarms.copy().items():
            try:
                fix_time_value = alarm.get("fix_time")
                logger.debug(f"[REMINDER] Сбой {alarm_id}, fix_time: {fix_time_value}")
                if isinstance(fix_time_value, str):
                    fix_time = datetime.fromisoformat(fix_time_value)
                elif isinstance(fix_time_value, datetime):
                    fix_time = fix_time_value
                else:
                    continue

                reminder_time = fix_time - timedelta(minutes=5)
                if now >= reminder_time:
                    user_id = alarm["user_id"]
                    if alarm.get("reminded", False):
                        logger.info(f"[REMINDER] Сбой {alarm_id} уже напоминали")
                        continue

                    alarm["reminded"] = True
                    logger.info(f"[REMINDER] Подготовка уведомления для сбоя {alarm_id} пользователю {user_id}")

                    try:
                        msg = await bot.send_message(
                            user_id,
                            f"⚠️ До окончания сбоя {alarm_id} осталось 5 минут.\nПродлевать?",
                            reply_markup=create_reminder_keyboard()
                        )
                        bot_state.user_states[user_id] = {
                            "type": "reminder",
                            "alarm_id": alarm_id,
                            "chat_id": msg.chat.id,
                            "message_id": msg.message_id
                        }
                        logger.info(f"[REMINDER] Уведомление отправлено пользователю {user_id}")
                    except Exception as e:
                        logger.error(f"[REMINDER] Ошибка отправки уведомления: {e}")
                        alarm["reminded"] = False

            except KeyError as ke:
                logger.warning(f"[REMINDER] Отсутствует ключ {ke} в сбое {alarm_id}")
            except Exception as e:
                logger.error(f"[REMINDER] Ошибка обработки сбоя {alarm_id}: {e}", exc_info=True)

        await asyncio.sleep(60)  # Проверяем каждую минуту


# --- Обработка действий из уведомления ---
@router.callback_query(lambda call: call.data.startswith("reminder_"))
async def handle_reminder_action(call: CallbackQuery, state: FSMContext):
    action = call.data.split("_", 1)[1]  # ✅ Всегда вернёт "stop" или "extend"
    user_id = call.from_user.id
    user_state = bot_state.user_states.get(user_id)
    logger.info(f"[{user_id}] Нажата кнопка напоминания: {action}")

    if not user_state or user_state.get("type") != "reminder":
        logger.warning(f"[{user_id}] Уведомление устарело или не существует")
        await call.answer("❌ Это уведомление устарело")
        return

    alarm_id = user_state["alarm_id"]
    alarm = bot_state.active_alarms.get(alarm_id)

    if not alarm:
        logger.warning(f"[{user_id}] Сбой {alarm_id} не найден при обработке напоминания")
        await call.message.edit_text("❌ Сбой уже завершён")
        if user_id in bot_state.user_states:
            del bot_state.user_states[user_id]
        return

    if action == "stop":
        logger.info(f"[{user_id}] Сбой {alarm_id} остановлен по напоминанию")
        text = (
            f"✅ <b>Сбой завершён</b>\n"
            f"• <b>Проблема:</b> {alarm['issue']}\n"
        )
        del bot_state.active_alarms[alarm_id]
        await call.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], text, parse_mode="HTML")
        await call.message.edit_text("🚫 Сбой завершён по решению автора")
        if user_id in bot_state.user_states:
            del bot_state.user_states[user_id]
        await bot_state.save_state()
        logger.info(f"[{user_id}] Сбой {alarm_id} остановлен через напоминание")

    elif action == "extend":
        logger.info(f"[{user_id}] Запрошено продление сбоя {alarm_id}")
        await call.message.edit_text("На сколько продлить сбой?", reply_markup=create_extension_time_keyboard())
        await state.update_data(alarm_id=alarm_id)
        await state.set_state(ReminderStates.WAITING_FOR_EXTENSION)
        logger.info(f"[{user_id}] Перешёл в состояние WAITING_FOR_EXTENSION")

    await call.answer()


# --- Продление сбоя из уведомления ---
@router.callback_query(ReminderStates.WAITING_FOR_EXTENSION)
async def handle_reminder_extension(call: CallbackQuery, state: FSMContext):
    duration = call.data
    data = await state.get_data()
    alarm_id = data["alarm_id"]
    alarm = bot_state.active_alarms.get(alarm_id)

    if not alarm:
        logger.warning(f"[{call.from_user.id}] Сбой {alarm_id} не найден при продлении")
        await call.message.edit_text("❌ Сбой не найден")
        await call.answer()
        return

    logger.info(f"[{call.from_user.id}] Выбрано продление сбоя {alarm_id}: {duration}")
    fix_time_value = alarm.get("fix_time")
    old_end = datetime.fromisoformat(fix_time_value) if isinstance(fix_time_value, str) else fix_time_value
    delta = timedelta(minutes=30) if duration == "extend_30_min" else timedelta(hours=1)

    new_end = old_end + delta
    alarm["fix_time"] = new_end.isoformat()
    logger.info(f"[{call.from_user.id}] Новое время окончания: {new_end.isoformat()}")

    text = (
        f"🔄 <b>Сбой продлён</b>\n"
        f"• <b>Проблема:</b> {alarm['issue']}\n"
        f"• <b>Новое время окончания:</b> {new_end.strftime('%d.%m.%Y %H:%M')}\n"
    )

    await call.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], text, parse_mode="HTML")
    logger.info(f"[{call.from_user.id}] Сообщение о продлении отправлено в канал")
    await call.message.edit_text(f"🕒 Сбой {alarm_id} продлён до {new_end.strftime('%d.%m.%Y %H:%M')}")
    await bot_state.save_state()
    logger.info(f"[{call.from_user.id}] Сохранено состояние после продления")
    await state.clear()
    logger.info(f"[{call.from_user.id}] FSM очищена после продления")
    await call.answer()