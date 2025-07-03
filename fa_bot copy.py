import asyncio
import logging
import os
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import CONFIG
from utils.create_jira_fa import create_failure_issue

# Настройка логирования
def setup_logging():
    # Формат логов
    log_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

    # Логирование в файл
    file_handler = logging.FileHandler("fa_bot.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Логирование в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Основная настройка логгера
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[file_handler, console_handler]
    )

setup_logging()
logger = logging.getLogger(__name__)

# Проверка наличия токена
if "TELEGRAM" not in CONFIG or "TOKEN" not in CONFIG["TELEGRAM"]:
    logger.critical("❌ Токен Telegram не найден в конфиге")
    sys.exit(1)

# Инициализация бота и диспетчера
bot = Bot(
    token=CONFIG["TELEGRAM"]["TOKEN"],
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# Состояния FSM
class FAStates(StatesGroup):
    waiting_for_summary = State()
    waiting_for_description = State()
    waiting_for_level = State()
    waiting_for_service = State()
    waiting_for_naumen_type = State()
    waiting_for_stream_1c = State()
    waiting_for_influence = State()
    waiting_for_confirmation = State()

# Списки опций
PROBLEM_LEVELS = [
    "Замедление работы сервиса",
    "Полная недоступность сервиса",
    "Частичная недоступность сервиса",
    "Проблемы в работе сервиса",
    "Потенциальная недоступность сервиса"
]

PROBLEM_SERVICES = [
    "Naumen", "Электронная почта", "УТЦ", "УТ Юнион", "1С УТ СПБ", "1С УТ СЗФО",
    "1С УТ МСК", "1С ЦФС", "УТ СПБ+УТ СЗФО+ УТ МСК", "LMS", "Проблема с обменами",
    "Сеть и интернет 1 подразделения", "Удалённый рабочий стол RDP (trm)",
    "Удалённый рабочий стол RDP для КЦ (retrm)", "VPN офисный", "VPN ДО КЦ",
    "Стационарная телефония", "Мобильная телефония", "Сетевое хранилище (Диск Х)",
    "Сайт Petrovich.ru", "Чат на сайте", "Jira", "Confluence", "Petlocal.ru",
    "Электроэнергия", "Телеопти/Май тайм", "Сервис оплаты", "Jira + Confluence",
    "b2b.stdp.ru", "Skype for business(Lync)", "DocsVision (DV)", "УТ СПБ",
    "ЗУП", "HR-Link", "WMS", "Мобильное приложение", "Другое"
]

NAUMEN_FAILURE_TYPES = [
    "Голосовой канал", "Авторизация", "Softphone", "Анкета", "Кейсы с сайта",
    "Почтовый канал", "Чат (VK, WA, Telegram, Webim)", "Отчёты", "Другое"
]

STREAM_1C_OPTIONS = [
    "Интеграция", "Коммерция", "Маркетинг", "ОПТ", "ПиКК", "Розница (СТЦ/КЦ)",
    "Сервисы оплат", "Складская логистика", "Транспортная логистика",
    "Финансы", "ЭДО"
]

INFLUENCE_OPTIONS = ["Клиенты", "Бизнес-функция", "Сотрудники"]

# Клавиатуры
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🚨 Создать задачу FA", callback_data="create_fa"))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()

def get_keyboard_from_list(options, add_cancel=True, is_optional=False):
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(options):
        # Используем индекс как callback_data
        builder.add(InlineKeyboardButton(text=option, callback_data=f"opt_{i}"))
    if add_cancel:
        if is_optional:
            builder.add(InlineKeyboardButton(text="Не заполнять", callback_data="skip"))
        builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()

# Обработчики
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для создания задач FA.\n"
        "Нажмите кнопку 'Создать задачу FA' чтобы начать.",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "create_fa")
async def create_fa_task(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(FAStates.waiting_for_summary)
    await callback_query.message.answer(
        "Введите краткое описание проблемы (заголовок задачи):",
        reply_markup=ReplyKeyboardRemove()
    )
    await callback_query.answer()

@router.callback_query(F.data == "cancel")
async def cancel_operation(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.answer("Создание задачи отменено.", reply_markup=get_main_keyboard())
    await callback_query.answer()

@router.callback_query(F.data == "skip")
async def skip_field(callback_query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == FAStates.waiting_for_naumen_type:
        await state.update_data(naumen_type=None)
        await state.set_state(FAStates.waiting_for_stream_1c)
        await callback_query.message.answer(
            "Выберите поток 1С (или нажмите 'Не заполнять' чтобы пропустить):",
            reply_markup=get_keyboard_from_list(STREAM_1C_OPTIONS, is_optional=True)
        )
    elif current_state == FAStates.waiting_for_stream_1c:
        await state.update_data(stream_1c=None)
        await state.set_state(FAStates.waiting_for_influence)
        await callback_query.message.answer(
            "Выберите влияние на:",
            reply_markup=get_keyboard_from_list(INFLUENCE_OPTIONS)
        )
    await callback_query.answer()

@router.callback_query(F.data.startswith("opt_"))
async def process_option(callback_query: types.CallbackQuery, state: FSMContext):
    option_index = int(callback_query.data.replace("opt_", ""))
    current_state = await state.get_state()
    
    if current_state == FAStates.waiting_for_level:
        if option_index < len(PROBLEM_LEVELS):
            option = PROBLEM_LEVELS[option_index]
            await state.update_data(level=option)
            await state.set_state(FAStates.waiting_for_service)
            await callback_query.message.answer(
                "Выберите затронутый сервис:",
                reply_markup=get_keyboard_from_list(PROBLEM_SERVICES)
            )
    elif current_state == FAStates.waiting_for_service:
        if option_index < len(PROBLEM_SERVICES):
            option = PROBLEM_SERVICES[option_index]
            await state.update_data(service=option)
            await state.set_state(FAStates.waiting_for_naumen_type)
            await callback_query.message.answer(
                "Выберите тип проблемы в Naumen (или нажмите 'Не заполнять' чтобы пропустить):",
                reply_markup=get_keyboard_from_list(NAUMEN_FAILURE_TYPES, is_optional=True)
            )
    elif current_state == FAStates.waiting_for_naumen_type:
        if option_index < len(NAUMEN_FAILURE_TYPES):
            option = NAUMEN_FAILURE_TYPES[option_index]
            await state.update_data(naumen_type=option)
            await state.set_state(FAStates.waiting_for_stream_1c)
            await callback_query.message.answer(
                "Выберите поток 1С (или нажмите 'Не заполнять' чтобы пропустить):",
                reply_markup=get_keyboard_from_list(STREAM_1C_OPTIONS, is_optional=True)
            )
    elif current_state == FAStates.waiting_for_stream_1c:
        if option_index < len(STREAM_1C_OPTIONS):
            option = STREAM_1C_OPTIONS[option_index]
            await state.update_data(stream_1c=option)
            await state.set_state(FAStates.waiting_for_influence)
            await callback_query.message.answer(
                "Выберите влияние на:",
                reply_markup=get_keyboard_from_list(INFLUENCE_OPTIONS)
            )
    elif current_state == FAStates.waiting_for_influence:
        if option_index < len(INFLUENCE_OPTIONS):
            option = INFLUENCE_OPTIONS[option_index]
            await state.update_data(influence=option)
            data = await state.get_data()
            
            # Формируем текст для подтверждения
            confirmation_text = (
                "Проверьте данные задачи:\n\n"
                f"Заголовок: {data['summary']}\n"
                f"Описание: {data['description']}\n"
                f"Уровень: {data['level']}\n"
                f"Сервис: {data['service']}\n"
            )
            
            if data.get('naumen_type'):
                confirmation_text += f"Тип в Naumen: {data['naumen_type']}\n"
            if data.get('stream_1c'):
                confirmation_text += f"Поток 1С: {data['stream_1c']}\n"
            if data.get('influence'):
                confirmation_text += f"Влияние на: {data['influence']}\n"
            
            confirmation_text += "\nВсё верно?"
            
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"))
            builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
            builder.adjust(2)
            
            await state.set_state(FAStates.waiting_for_confirmation)
            await callback_query.message.answer(confirmation_text, reply_markup=builder.as_markup())
    
    await callback_query.answer()

@router.callback_query(F.data == "confirm")
async def confirm_task(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    try:
        # Создаем задачу в Jira
        jira_response = create_failure_issue(
            summary=data['summary'],
            description=data['description'],
            problem_level=data['level'],
            problem_service=data['service'],
            naumen_failure_type=data.get('naumen_type'),
            stream_1c=data.get('stream_1c'),
            time_start_problem=datetime.now().strftime("%Y-%m-%d %H:%M"),
            influence=data.get('influence')
        )
        
        logger.info(f"Ответ от Jira: {jira_response}")
        
        if jira_response and 'key' in jira_response:
            task_key = jira_response['key']
            task_url = f"https://jira.petrovich.tech/browse/{task_key}"
            await callback_query.message.answer(
                f"✅ Задача успешно создана!\n"
                f"Номер задачи: {task_key}\n"
                f"Ссылка: {task_url}",
                reply_markup=get_main_keyboard()
            )
        else:
            error_msg = f"Не удалось создать задачу в Jira. Ответ: {jira_response}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        logger.error(f"Ошибка при создании задачи в Jira: {str(e)}", exc_info=True)
        await callback_query.message.answer(
            "❌ Произошла ошибка при создании задачи. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
    
    await state.clear()
    await callback_query.answer()

@router.message(FAStates.waiting_for_summary)
async def process_summary(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Создание задачи отменено.", reply_markup=get_main_keyboard())
        return

    await state.update_data(summary=message.text)
    await state.set_state(FAStates.waiting_for_description)
    await message.answer(
        "Опишите проблему подробно:",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(FAStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Создание задачи отменено.", reply_markup=get_main_keyboard())
        return

    await state.update_data(description=message.text)
    await state.set_state(FAStates.waiting_for_level)
    await message.answer(
        "Выберите уровень проблемы:",
        reply_markup=get_keyboard_from_list(PROBLEM_LEVELS)
    )

# Запуск бота
async def main():
    logger.info("🚀 Запуск FA бота...")
    
    # Регистрация роутера
    dp.include_router(router)
    
    # Установка команд
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="Запустить бота"),
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Команды установлены")

    try:
        logger.info("🤖 FA бот начал работу")
        await dp.start_polling(bot)
    finally:
        logger.info("🛑 FA бот остановлен")
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 FA бот остановлен пользователем") 