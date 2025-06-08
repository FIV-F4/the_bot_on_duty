# handlers/screenshot.py

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

import asyncio
import logging
from typing import Optional

# Импорты из модулей
from selenium_utils import make_confluence_screenshot, make_jira_screenshot, make_confluence_screenshot_page
from config import CONFIG
from keyboards import create_view_selection_keyboard, create_main_keyboard, create_cancel_keyboard
from utils.helpers import is_admin  # <-- Добавили импорт функции проверки админства

logger = logging.getLogger(__name__)
router = Router()


# --- Состояния ---
class ViewStates(StatesGroup):
    WAITING_URL = State()


# --- Обработчики ---

@router.message(Command("view"))
@router.message(F.text == "📸 JIRA/Confluence")
async def view_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Пользователь выбрал '📸 JIRA/Confluence'")

    if not is_admin(user_id):
        await message.answer("❌ У вас нет прав для выполнения этой команды ❌", parse_mode='HTML')
        return

    await message.answer(
        "Выберите действие:",
        reply_markup=create_view_selection_keyboard()
    )


@router.message(F.text == "📅 Календарь работ")
async def take_calendar_screenshot(message: Message):
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Запрошена команда 'Календарь работ'")

    if not is_admin(user_id):
        await message.answer("❌ У вас нет прав для выполнения этой команды ❌", parse_mode='HTML')
        return

    msg = await message.answer("📸 Делаю скриншот календаря...", reply_markup=ReplyKeyboardRemove())

    try:
        success = await asyncio.wait_for(
            asyncio.to_thread(make_confluence_screenshot),
            timeout=CONFIG.get("TASK_TIMEOUT", 30)
        )
        if success:
            await message.answer_photo(
                photo=FSInputFile("screenshot.png"),
                caption=f"🗓️ Вот календарь работ!\n[Ссылка на страницу]({CONFIG['CONFLUENCE']['TARGET_URL']})",
                parse_mode='Markdown',
                reply_markup=create_main_keyboard()
            )
        else:
            await message.answer("❌ Не удалось сделать скриншот", reply_markup=create_main_keyboard())
    except asyncio.TimeoutError:
        await message.answer("⏳ Превышено время ожидания при создании скриншота", reply_markup=create_main_keyboard())
    except Exception as e:
        logger.error(f"[{user_id}] Ошибка при работе с Confluence: {str(e)}")
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=create_main_keyboard())
    finally:
        try:
            await message.answer_chat_action("delete_message")  # Более надёжный способ удаления
            await message.delete()  # Удаляем временное сообщение
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить сообщение: {e}")


@router.message(F.text == "🔍 Посмотреть JIRA")
async def watch_jira(message: Message, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Запрошена команда 'Посмотреть JIRA'")

    if not is_admin(user_id):
        await message.answer("❌ У вас нет прав для выполнения этой команды ❌", parse_mode='HTML')
        return

    await state.set_state(ViewStates.WAITING_URL)
    await message.answer(
        "🔗 Введите URL задачи в JIRA для скриншота:",
        reply_markup=create_cancel_keyboard()
    )


@router.message(F.text == "🌐 Посмотреть Confluence")
async def watch_confluence(message: Message, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Запрошена команда 'Посмотреть Confluence'")

    if not is_admin(user_id):
        await message.answer("❌ У вас нет прав для выполнения этой команды ❌", parse_mode='HTML')
        return

    await state.set_state(ViewStates.WAITING_URL)
    await message.answer(
        "🔗 Введите URL страницы в Confluence для скриншота:",
        reply_markup=create_cancel_keyboard()
    )


@router.message(ViewStates.WAITING_URL)
async def process_view_url(message: Message, state: FSMContext):
    url = message.text.strip()
    user_id = message.from_user.id

    if url == "❌ Отмена":
        await state.clear()
        await message.answer("🚫 Действие отменено", reply_markup=create_main_keyboard())
        return

    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer("⚠️ Некорректный URL. Введите полный адрес.", reply_markup=create_cancel_keyboard())
        return

    msg = await message.answer("📸 Делаю скриншот страницы...", reply_markup=ReplyKeyboardRemove())

    try:
        is_jira = "jira" in url.lower()
        success = False

        if is_jira:
            success = await asyncio.wait_for(
                asyncio.to_thread(make_jira_screenshot, url),
                timeout=CONFIG.get("TASK_TIMEOUT", 30)
            )
        else:
            success = await asyncio.wait_for(
                asyncio.to_thread(make_confluence_screenshot_page, url),
                timeout=CONFIG.get("TASK_TIMEOUT", 30)
            )

        if success:
            caption = f"📌 Скриншот страницы:\n{url}"
            await message.answer_photo(
                photo=FSInputFile("screenshot.png"),
                caption=caption,
                parse_mode='Markdown',
                reply_markup=create_view_selection_keyboard()
            )
        else:
            await message.answer("❌ Не удалось получить скриншот.", reply_markup=create_main_keyboard())
    except asyncio.TimeoutError:
        await message.answer("⏳ Превышено время ожидания при создании скриншота", reply_markup=create_main_keyboard())
    except Exception as e:
        logger.error(f"[{user_id}] Ошибка при работе с JIRA/Confluence: {str(e)}")
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=create_main_keyboard())
    finally:
        try:
            await message.delete()
            await bot.delete_message(msg.chat.id, msg.message_id)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить сообщение: {e}")
        await state.clear()