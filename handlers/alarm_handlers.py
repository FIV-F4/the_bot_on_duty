# handlers/alarm_handlers.py
import re
import logging
import uuid
from datetime import datetime as dt, timedelta
from typing import Optional
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot

# Импорты из ваших модулей
from keyboards import (
    create_cancel_keyboard,
    create_main_keyboard,
    create_message_type_keyboard,
    create_confirmation_keyboard,
    create_level_keyboard,
    create_service_keyboard
)
from utils.helpers import NewMessageStates, parse_duration, get_user_name, is_admin
from bot_state import bot_state
from config import CONFIG, PROBLEM_LEVELS, PROBLEM_SERVICES, INFLUENCE_OPTIONS
from utils.create_jira_fa import create_failure_issue

logger = logging.getLogger(__name__)
router = Router()

DATETIME_FORMAT = "%d.%m.%Y %H:%M"

# Обновляем состояния
class NewMessageStates(StatesGroup):
    SELECTING_TYPE = State()
    ENTER_TITLE = State()  # Новое состояние для заголовка
    ENTER_DESCRIPTION = State()  # Новое состояние для описания
    ENTER_LEVEL = State()  # Новое состояние для уровня проблемы
    ENTER_SERVICE = State()  # Новое состояние для сервиса
    ENTER_FIX_TIME = State()
    ENTER_START_TIME = State()
    ENTER_END_TIME = State()
    ENTER_UNAVAILABLE_SERVICES = State()
    ENTER_MESSAGE_TEXT = State()
    CONFIRMATION = State()


@router.message(Command("new_message"))
@router.message(F.text == "📢 Сообщить")
async def new_message_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Пользователь начал создание нового сообщения")
    if not is_admin(user_id):
        logger.warning(f"[{user_id}] Попытка начать создание сообщения без прав администратора")
        await message.answer("❌ У вас нет прав для выполнения этой команды", parse_mode='HTML')
        return
    await state.clear()
    logger.info(f"[{user_id}] Состояние очищено")
    await message.answer("Выберите тип сообщения:", reply_markup=create_message_type_keyboard())
    await state.set_state(NewMessageStates.SELECTING_TYPE)


@router.callback_query(F.data.startswith("message_type_"))
async def handle_message_type(call: CallbackQuery, state: FSMContext):
    msg_type = call.data.split("_")[-1]  # 'alarm', 'maintenance', 'regular'
    logger.info(f"[{call.from_user.id}] Выбран тип сообщения: {msg_type}")
    if msg_type == "alarm":
        await state.set_state(NewMessageStates.ENTER_TITLE)
        await call.message.answer("✏️ Введите заголовок проблемы:", reply_markup=create_cancel_keyboard())
    elif msg_type == "maintenance":
        await state.set_state(NewMessageStates.ENTER_TITLE)
        await call.message.answer("🔧 Введите заголовок работ:", reply_markup=create_cancel_keyboard())
    elif msg_type == "regular":
        await state.set_state(NewMessageStates.ENTER_MESSAGE_TEXT)
        await call.message.answer("💬 Введите текст сообщения:", reply_markup=create_cancel_keyboard())
    await state.update_data(type=msg_type)
    await call.answer()


@router.message(NewMessageStates.ENTER_TITLE)
async def enter_title(message: Message, state: FSMContext):
    title = message.text.strip()
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Введен заголовок: {title[:30]}...")
    if title == "❌ Отмена":
        logger.info(f"[{user_id}] Действие отменено пользователем")
        await state.clear()
        await message.answer("🚫 Действие отменено", reply_markup=create_main_keyboard())
        return
    await state.update_data(title=title)
    await state.set_state(NewMessageStates.ENTER_DESCRIPTION)
    await message.answer("✏️ Опишите проблему подробно:", reply_markup=create_cancel_keyboard())


@router.message(NewMessageStates.ENTER_DESCRIPTION)
async def enter_description(message: Message, state: FSMContext):
    description = message.text.strip()
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Введено описание: {description[:30]}...")
    if description == "❌ Отмена":
        logger.info(f"[{user_id}] Действие отменено пользователем")
        await state.clear()
        await message.answer("🚫 Действие отменено", reply_markup=create_main_keyboard())
        return
    await state.update_data(description=description)
    data = await state.get_data()
    if data["type"] == "alarm":
        # Автоматически устанавливаем уровень
        await state.update_data(level="Потенциальная недоступность сервиса")
        await state.set_state(NewMessageStates.ENTER_SERVICE)
        await message.answer("Выберите затронутый сервис:", reply_markup=create_service_keyboard())
    elif data["type"] == "maintenance":
        logger.info(f"[{user_id}] Запрошено время начала работ")
        await message.answer(
            "⌛ Введите время начала работ в формате:\n"
            "• Например: «27.05.2025 16:00»",
            reply_markup=create_cancel_keyboard()
        )
        await state.set_state(NewMessageStates.ENTER_START_TIME)


@router.callback_query(F.data.startswith("lvl_"))
async def process_level(callback: CallbackQuery, state: FSMContext):
    level_index = int(callback.data.replace("lvl_", ""))
    level = PROBLEM_LEVELS[level_index]
    await state.update_data(level=level)
    await state.set_state(NewMessageStates.ENTER_SERVICE)
    await callback.message.edit_text(
        "Выберите затронутый сервис:",
        reply_markup=create_service_keyboard()
    )


@router.callback_query(F.data.startswith("svc_"))
async def process_service(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    service_index = int(callback.data.replace("svc_", ""))
    service = PROBLEM_SERVICES[service_index]
    logger.info(f"[{user_id}] Выбран сервис: {service}")
    await state.update_data(service=service)
    
    # Автоматически устанавливаем время +1 час от текущего
    now = dt.now()
    fix_time = now + timedelta(hours=1)
    await state.update_data(fix_time=fix_time.isoformat())
    
    # Показываем предварительный просмотр
    data = await state.get_data()
    title = data["title"]
    description = data["description"]
    service = data["service"]
    preview_text = (
        "📄 <b>Предварительный просмотр:</b>\n"
        f"🚨 <b>Технический сбой</b>\n"
        f"• <b>Проблема:</b> {title}\n"
        f"• <b>Описание:</b> {description}\n"
        f"• <b>Сервис:</b> {service}\n"
        f"• <b>Исправим до:</b> {fix_time.strftime(DATETIME_FORMAT)}"
    )
    await state.update_data(preview_text=preview_text)

    # ИСПРАВЛЕНИЕ: Используем новое сообщение вместо редактирования
    logger.info(f"[{user_id}] Отправляем предварительный просмотр с инлайн клавиатурой")
    await callback.message.answer(
        preview_text,
        parse_mode='HTML',
        reply_markup=create_confirmation_keyboard()
    )
    await state.set_state(NewMessageStates.CONFIRMATION)
    await callback.answer()


@router.message(NewMessageStates.ENTER_START_TIME)
async def enter_start_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Введено время начала: {time_str}")
    if time_str == "❌ Отмена":
        logger.info(f"[{user_id}] Отмена на этапе ENTER_START_TIME")
        await state.clear()
        await message.answer("🚫 Действие отменено", reply_markup=create_main_keyboard())
        return
    try:
        start_time = dt.strptime(time_str, DATETIME_FORMAT)
        await state.update_data(start_time=start_time.isoformat())
        logger.debug(f"[{user_id}] Время начала установлено: {start_time.isoformat()}")
        await message.answer(
            "⌛ Введите время окончания работ в формате:\n"
            "• Например: «27.05.2025 16:00»",
            reply_markup=create_cancel_keyboard()
        )
        await state.set_state(NewMessageStates.ENTER_END_TIME)
    except ValueError as e:
        logger.warning(f"[{user_id}] Неверный формат даты: {e}")
        await message.answer(
            "⚠️ Неверный формат времени.\n"
            "Введите дату и время в формате:\n"
            "• Пример: «27.05.2025 14:00»",
            reply_markup=create_cancel_keyboard()
        )


@router.message(NewMessageStates.ENTER_END_TIME)
async def enter_end_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Введено время окончания: {time_str}")
    if time_str == "❌ Отмена":
        logger.info(f"[{user_id}] Отмена на этапе ENTER_END_TIME")
        await state.clear()
        await message.answer("🚫 Действие отменено", reply_markup=create_main_keyboard())
        return
    try:
        data = await state.get_data()
        start_time = dt.fromisoformat(data["start_time"])
        end_time = dt.strptime(time_str, DATETIME_FORMAT)
        if end_time < start_time:
            raise ValueError("Время окончания не может быть раньше начала")
        await state.update_data(end_time=end_time.isoformat())
        logger.debug(f"[{user_id}] Время окончания установлено: {end_time.isoformat()}")
        await message.answer(
            "🔌 Что будет недоступно во время работ?",
            reply_markup=create_cancel_keyboard()
        )
        await state.set_state(NewMessageStates.ENTER_UNAVAILABLE_SERVICES)
    except ValueError as e:
        logger.error(f"[{user_id}] Ошибка при парсинге времени окончания: {str(e)}", exc_info=True)
        await message.answer(
            "⏰ Введите корректное время окончания:\n"
            "• Формат: «дд.мм.гггг чч:мм»\n"
            "• Пример: «27.05.2025 16:00»",
            reply_markup=create_cancel_keyboard()
        )


@router.message(NewMessageStates.ENTER_UNAVAILABLE_SERVICES)
async def enter_unavailable_services(message: Message, state: FSMContext):
    services = message.text.strip()
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Введены недоступные сервисы: {services[:30]}...")
    if services == "❌ Отмена":
        logger.info(f"[{user_id}] Отмена на этапе ENTER_UNAVAILABLE_SERVICES")
        await state.clear()
        await message.answer("🚫 Действие отменено", reply_markup=create_main_keyboard())
        return
    await state.update_data(unavailable_services=services)
    data = await state.get_data()
    title = data["title"]
    description = data["description"]
    start_time = dt.fromisoformat(data["start_time"])
    end_time = dt.fromisoformat(data["end_time"])
    preview_text = (
        "📄 <b>Предварительный просмотр:</b>\n"
        f"🔧 <b>Регламентные работы</b>\n"
        f"• <b>Заголовок:</b> {title}\n"
        f"• <b>Описание:</b> {description}\n"
        f"• <b>Начало:</b> {start_time.strftime(DATETIME_FORMAT)}\n"
        f"• <b>Конец:</b> {end_time.strftime(DATETIME_FORMAT)}\n"
        f"• <b>Недоступно:</b> {services}"
    )
    await state.update_data(preview_text=preview_text)
    await message.answer(preview_text, parse_mode='HTML', reply_markup=create_confirmation_keyboard())
    await state.set_state(NewMessageStates.CONFIRMATION)


@router.message(NewMessageStates.ENTER_MESSAGE_TEXT)
async def enter_message_text(message: Message, state: FSMContext):
    text = message.text.strip()
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Введён текст сообщения: {text[:30]}...")
    if text == "❌ Отмена":
        logger.info(f"[{user_id}] Отмена на этапе ENTER_MESSAGE_TEXT")
        await state.clear()
        await message.answer("🚫 Действие отменено", reply_markup=create_main_keyboard())
        return
    await state.update_data(message_text=text)
    logger.debug(f"[{user_id}] Текст сохранён: {text[:50]}...")
    await message.answer("✅ Подтвердите отправку", reply_markup=create_confirmation_keyboard())
    await state.set_state(NewMessageStates.CONFIRMATION)


# Удалена функция confirm_send(message: Message, ...), так как используется только callback


@router.callback_query(F.data == "confirm_send")
async def confirm_send_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    logger.info(f"[{user_id}] Подтверждение отправки через callback")
    data = await state.get_data()
    msg_type = data["type"]

    try:
        if msg_type == "alarm":
            issue = data["title"]
            fix_time = dt.fromisoformat(data["fix_time"])
            # Пытаемся создать задачу в Jira
            try:
                jira_response = create_failure_issue(
                    summary=issue,
                    description=data["description"],
                    problem_level="Потенциальная недоступность сервиса",
                    problem_service=data["service"],
                    time_start_problem=dt.now().strftime("%Y-%m-%d %H:%M"),
                    influence="Клиенты"
                )
                if jira_response and 'key' in jira_response:
                    alarm_id = jira_response['key']
                    jira_url = f"https://jira.petrovich.tech/browse/{alarm_id}"
                    logger.info(f"[{user_id}] Задача в Jira создана: {alarm_id}")
                else:
                    raise Exception("Не удалось получить ID задачи из Jira")
            except Exception as jira_error:
                logger.error(f"[{user_id}] Ошибка создания задачи в Jira: {str(jira_error)}")
                alarm_id = str(uuid.uuid4())[:4]
                jira_url = None
                logger.info(f"[{user_id}] Используем локальный ID: {alarm_id}")

            bot_state.active_alarms[alarm_id] = {
                "issue": issue,
                "fix_time": fix_time,
                "user_id": user_id,
                "created_at": dt.now().isoformat()
            }

            base_text = (
                f"🚨 <b>Технический сбой</b>\n"
                f"• <b>Задача в Jira:</b> <a href='{jira_url}'>{alarm_id}</a>\n"
                f"• <b>Сервис:</b> {data['service']}\n"
                f"• <b>Проблема:</b> {data['title']}\n"
                f"• <b>Описание:</b> {data['description']}\n"
                f"• <i>Ссылка в Ктолк: https://petrovich.ktalk.ru/emergencyteam  </i>\n"
            )

            chat_message = (
                f"🚨 <b>Технический сбой</b>\n"
                f"• <b>Проблема:</b> {data['title']}\n"
                f"• <b>Сервис:</b> {data['service']}\n"
                f"• <b>Исправим до:</b> {fix_time.strftime(DATETIME_FORMAT)}\n"
                f"• <i>Мы уже работаем над устранением сбоя. Спасибо за ваше терпение и понимание!</i>"
            )

            await callback.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], chat_message, parse_mode='HTML')

            scm_channel_id = CONFIG["TELEGRAM"].get("SCM_CHANNEL_ID")
            if scm_channel_id:
                topic = await callback.bot.create_forum_topic(chat_id=scm_channel_id, name=f"🔥{alarm_id} {data['title'][:20]}...")
                await callback.bot.send_message(
                    chat_id=scm_channel_id,
                    message_thread_id=topic.message_thread_id,
                    text=base_text,
                    parse_mode='HTML'
                )
                logger.info(f"[{user_id}] Тема создана: {topic.message_thread_id}")

            user_message = f"✅ Сбой зарегистрирован! ID: <code>{alarm_id}</code>"
            if jira_url:
                user_message += f"\n🔗 <a href='{jira_url}'>Задача в Jira</a>"

            await callback.message.edit_text(user_message, parse_mode='HTML', reply_markup=None)
            await bot_state.save_state()
            await state.clear()

        elif msg_type == "maintenance":
            work_id = str(uuid.uuid4())[:4]
            description = data["description"]
            start_time = dt.fromisoformat(data["start_time"])
            end_time = dt.fromisoformat(data["end_time"])
            unavailable_services = data.get("unavailable_services", "не указано")

            bot_state.active_maintenances[work_id] = {
                "description": description,
                "start_time": start_time,
                "end_time": end_time,
                "unavailable_services": unavailable_services,
                "user_id": user_id,
                "created_at": dt.now().isoformat()
            }

            maint_text = (
                f"🔧 <b>Проводим плановые технические работы – станет ещё лучше!</b>\n"
                f"• <b>Описание:</b> {description}\n"
                f"• <b>Начало:</b> {start_time.strftime(DATETIME_FORMAT)}\n"
                f"• <b>Конец:</b> {end_time.strftime(DATETIME_FORMAT)}\n"
                f"• <b>Недоступно:</b> {unavailable_services}\n"
                f"• <i>Спасибо за понимание! Эти изменения – важный шаг к тому, чтобы сервис стал ещё удобнее и надёжнее для вас 💙</i>\n"
                f"• <i>Если возникнут вопросы – наша поддержка всегда на связи</i>\n"
                f"• <i>С заботой, Ваша команда Петрович-ТЕХ</i>"
            )

            await callback.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], maint_text, parse_mode='HTML')
            logger.info(f"[{user_id}] Работа {work_id} зарегистрирована")
            await callback.message.edit_text(
                f"✅ Работы зарегистрированы! ID: <code>{work_id}</code>",
                parse_mode='HTML',
                reply_markup=None
            )
            await bot_state.save_state()
            await state.clear()

        elif msg_type == "regular":
            message_text = data["message_text"]
            regular_text = (
                f"💬 <b>Сообщение от администратора:</b>\n"
                f"{message_text}\n"
            )
            await callback.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], regular_text, parse_mode='HTML')
            logger.info(f"[{user_id}] Обычное сообщение отправлено в канал")
            await callback.message.edit_text(
                "✅ Сообщение отправлено",
                reply_markup=None
            )
            await bot_state.save_state()
            await state.clear()

        else:
            logger.warning(f"[{user_id}] Неизвестный тип сообщения: {msg_type}")
            await callback.message.edit_text("❌ Неизвестный тип сообщения", reply_markup=None)
            await state.clear()

    except Exception as e:
        logger.error(f"[{user_id}] Ошибка при завершении отправки: {str(e)}", exc_info=True)
        await callback.message.edit_text("❌ Не удалось отправить сообщение", reply_markup=None)
        await state.clear()


@router.callback_query(F.data == "cancel")
async def cancel_action_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    logger.info(f"[{user_id}] Отмена действия через callback")
    await state.clear()
    await callback.message.edit_text("🚫 Действие отменено", reply_markup=None)
    await callback.message.answer("Выберите действие:", reply_markup=create_main_keyboard())
    await callback.answer()

@router.callback_query(F.data == "confirm_cancel")
async def cancel_send_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    logger.info(f"[{user_id}] Отмена отправки через callback")
    await state.clear()
    await callback.message.edit_text("🚫 Действие отменено", reply_markup=None)
    await callback.message.answer("Выберите действие:", reply_markup=create_main_keyboard())
    await callback.answer()