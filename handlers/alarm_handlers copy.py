# handlers/alarm_handlers.py
import re
import logging
import uuid
from datetime import datetime as dt, timedelta
from typing import Optional
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, InlineKeyboardBuilder
from aiogram import Bot

# Импорты из ваших модулей
from keyboards import create_cancel_keyboard, create_main_keyboard, create_message_type_keyboard, \
    create_confirmation_keyboard, create_level_keyboard, create_service_keyboard
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
        await state.set_state(NewMessageStates.ENTER_LEVEL)
        await message.answer("Выберите уровень проблемы:", reply_markup=create_level_keyboard())
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
    service_index = int(callback.data.replace("svc_", ""))
    service = PROBLEM_SERVICES[service_index]
    await state.update_data(service=service)
    await state.set_state(NewMessageStates.ENTER_FIX_TIME)
    
    # Создаем встроенную клавиатуру для отмены
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel")
    
    await callback.message.edit_text(
        "⏰ Укажите время восстановления:\n"
        "• Например: «15:00», «через 1 час»",
        reply_markup=builder.as_markup()
    )


@router.message(NewMessageStates.ENTER_FIX_TIME)
async def enter_fix_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    user_id = message.from_user.id
    now = dt.now()
    logger.info(f"[{user_id}] Введено время восстановления: {time_str}")

    if time_str == "❌ Отмена":
        logger.info(f"[{user_id}] Отмена на этапе ENTER_FIX_TIME")
        await state.clear()
        await message.answer("🚫 Действие отменено", reply_markup=create_main_keyboard())
        return

    try:
        fix_time = None
        if re.search(r"\d{1,2}:\d{2}", time_str):
            hour, minute = map(int, time_str.split(":"))
            fix_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if fix_time < now:
                fix_time += timedelta(days=1)
        elif "через" in time_str.lower():
            duration = parse_duration(time_str)
            if not duration:
                raise ValueError("Некорректная длительность")
            fix_time = now + duration
        else:
            duration = parse_duration(time_str)
            if not duration:
                raise ValueError("Неверный формат времени")
            fix_time = now + duration

        await state.update_data(fix_time=fix_time.isoformat())
        logger.debug(f"[{user_id}] Время восстановления установлено: {fix_time.isoformat()}")

        data = await state.get_data()
        title = data["title"]
        description = data["description"]
        level = data["level"]
        service = data["service"]
        preview_text = (
            "📄 <b>Предварительный просмотр:</b>\n"
            f"🚨 <b>Сбой</b>\n"
            f"• <b>Заголовок:</b> {title}\n"
            f"• <b>Описание:</b> {description}\n"
            f"• <b>Уровень:</b> {level}\n"
            f"• <b>Сервис:</b> {service}\n"
            f"• <b>Исправим до:</b> {fix_time.strftime(DATETIME_FORMAT)}"
        )

        await state.update_data(preview_text=preview_text)
        await message.answer(preview_text, parse_mode='HTML', reply_markup=create_confirmation_keyboard())
        await state.set_state(NewMessageStates.CONFIRMATION)

    except Exception as e:
        logger.error(f"[{user_id}] Ошибка регистрации сбоя: {str(e)}", exc_info=True)
        await message.answer(
            "⏰ Введите корректное время восстановления:\n"
            "• Например: «15:00» — точное время\n"
            "• Или: «через 1 час» — относительное время",
            reply_markup=create_cancel_keyboard()
        )


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


@router.message(NewMessageStates.CONFIRMATION)
async def confirm_send(message: Message, state: FSMContext):
    response = message.text.strip()
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Получен ответ подтверждения: {response}")

    if response == "Не отправлять":
        logger.info(f"[{user_id}] Отправка отменена пользователем")
        await state.clear()
        await message.answer("🚫 Действие отменено", reply_markup=create_main_keyboard())
        return

    elif response == "Отправить":
        data = await message.bot.get_me()
        bot_username = data.username
        username = await get_user_name(user_id, message.bot)
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
                        problem_level="Полная недоступность сервиса",  # Можно добавить выбор уровня в будущем
                        problem_service="Другое",  # Можно добавить выбор сервиса в будущем
                        time_start_problem=dt.now().strftime("%Y-%m-%d %H:%M"),
                        influence="Клиенты"  # Можно добавить выбор влияния в будущем
                    )
                    
                    if jira_response and 'key' in jira_response:
                        alarm_id = jira_response['key']  # Используем ID из Jira
                        jira_url = f"https://jira.petrovich.tech/browse/{alarm_id}"
                        logger.info(f"[{user_id}] Задача в Jira создана: {alarm_id}")
                    else:
                        raise Exception("Не удалось получить ID задачи из Jira")
                        
                except Exception as jira_error:
                    logger.error(f"[{user_id}] Ошибка создания задачи в Jira: {str(jira_error)}")
                    # Если не удалось создать в Jira, используем старый механизм
                    alarm_id = str(uuid.uuid4())[:4]
                    jira_url = None
                    logger.info(f"[{user_id}] Используем локальный ID: {alarm_id}")

                bot_state.active_alarms[alarm_id] = {
                    "issue": issue,
                    "fix_time": fix_time,
                    "user_id": user_id,
                    "created_at": dt.now().isoformat()
                }

                # Базовый текст сообщения
                base_text = (
                    f"🚨 <b>Сбой</b>\n"
                    f"• <b>ID:</b> <code>{alarm_id}</code>\n"
                    f"• <b>Заголовок:</b> {data['title']}\n"
                    f"• <b>Описание:</b> {data['description']}\n"
                    f"• <b>Уровень:</b> {data['level']}\n"
                    f"• <b>Сервис:</b> {data['service']}\n"
                    f"• <b>Исправим до:</b> {fix_time.strftime(DATETIME_FORMAT)}\n"
                    f"• <b>Автор:</b> {username}\n"
                    f"• <i>Инженеры уже работают над решением!</i>"
                )

                # Сообщение для чата (без ID, автора и описания)
                chat_message = (
                    f"🚨 <b>Сбой</b>\n"
                    f"• <b>Заголовок:</b> {data['title']}\n"
                    f"• <b>Уровень:</b> {data['level']}\n"
                    f"• <b>Сервис:</b> {data['service']}\n"
                    f"• <b>Исправим до:</b> {fix_time.strftime(DATETIME_FORMAT)}\n"
                    f"• <i>Инженеры уже работают над решением!</i>"
                )
                await message.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], chat_message, parse_mode='HTML')

                # Сообщение для темы (со ссылкой на Jira, если есть)
                topic_message = base_text
                if jira_url:
                    topic_message += f"\n• <b>Задача в Jira:</b> <a href='{jira_url}'>{alarm_id}</a>"

                scm_channel_id = CONFIG["TELEGRAM"].get("SCM_CHANNEL_ID")
                if scm_channel_id:
                    topic = await message.bot.create_forum_topic(chat_id=scm_channel_id, name=f"{alarm_id} {data['title'][:20]}...")
                    await message.bot.send_message(
                        chat_id=scm_channel_id,
                        message_thread_id=topic.message_thread_id,
                        text=topic_message,
                        parse_mode='HTML'
                    )
                    logger.info(f"[{user_id}] Тема создана: {topic.message_thread_id}")

                # Сообщение для пользователя
                user_message = f"✅ Сбой зарегистрирован! ID: <code>{alarm_id}</code>"
                if jira_url:
                    user_message += f"\n🔗 <a href='{jira_url}'>Задача в Jira</a>"

                logger.info(f"[{user_id}] Сбой {alarm_id} успешно зарегистрирован")
                await message.answer(
                    user_message,
                    parse_mode='HTML',
                    reply_markup=create_main_keyboard()
                )
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
                    f"🔧 <b>Регламентные работы</b>\n"
                    f"• <b>ID:</b> <code>{work_id}</code>\n"
                    f"• <b>Описание:</b> {description}\n"
                    f"• <b>Начало:</b> {start_time.strftime(DATETIME_FORMAT)}\n"
                    f"• <b>Конец:</b> {end_time.strftime(DATETIME_FORMAT)}\n"
                    f"• <b>Недоступно:</b> {unavailable_services}\n"
                    f"• <b>Автор:</b> {username}"
                )

                await message.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], maint_text, parse_mode='HTML')
                logger.info(f"[{user_id}] Работа {work_id} зарегистрирована")

                await message.answer(
                    f"✅ Работы зарегистрированы! ID: <code>{work_id}</code>",
                    parse_mode='HTML',
                    reply_markup=create_main_keyboard()
                )
                await bot_state.save_state()
                await state.clear()

            elif msg_type == "regular":
                message_text = data["message_text"]
                regular_text = (
                    f"💬 <b>Обычное сообщение</b>\n"
                    f"{message_text}\n"
                    f"• <b>Автор:</b> {username}"
                )

                await message.bot.send_message(CONFIG["TELEGRAM"]["ALARM_CHANNEL_ID"], regular_text, parse_mode='HTML')
                logger.info(f"[{user_id}] Обычное сообщение отправлено в канал")

                await message.answer(
                    "✅ Сообщение отправлено",
                    reply_markup=create_main_keyboard()
                )
                await bot_state.save_state()
                await state.clear()

            else:
                logger.warning(f"[{user_id}] Неизвестный тип сообщения: {msg_type}")
                await message.answer("❌ Неизвестный тип сообщения", reply_markup=create_main_keyboard())
                await state.clear()

        except Exception as e:
            logger.error(f"[{user_id}] Ошибка при завершении отправки: {str(e)}", exc_info=True)
            await message.answer("❌ Не удалось отправить сообщение", reply_markup=create_main_keyboard())
            await state.clear()

    else:
        logger.warning(f"[{user_id}] Некорректный ответ: {response}")
        data = await state.get_data()
        preview_text = data.get("preview_text", "")
        if preview_text:
            await message.answer(preview_text, parse_mode='HTML', reply_markup=create_confirmation_keyboard())
        else:
            await message.answer(
                "⚠️ Пожалуйста, выберите «Отправить» или «Не отправлять»",
                reply_markup=create_confirmation_keyboard()
            )