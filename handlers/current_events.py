# handlers/current_events.py
import logging
from aiogram.filters import Command
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot_state import bot_state  # Глобальный экземпляр BotState
from keyboards import create_event_list_keyboard

logger = logging.getLogger(__name__)
router = Router()


def create_refresh_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_selection"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="close_selection")
    )
    return builder.as_markup()


@router.message(Command("alarm_list"))
@router.message(F.text == "📕 Текущие события")
async def show_current_events(message: Message):
    user_id = message.from_user.id
    logger.info(f"[{user_id}] Пользователь запросил просмотр текущих событий")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚨 Сбои", callback_data="show_alarms")],
        [InlineKeyboardButton(text="🔧 Работы", callback_data="show_maintenances")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_selection")]
    ])
    await message.answer("Выберите, что вы хотите посмотреть:", reply_markup=keyboard)


@router.callback_query(lambda call: call.data in ["show_alarms", "show_maintenances"])
async def handle_list_callback(call: CallbackQuery):
    user_id = call.from_user.id
    choice = call.data
    logger.info(f"[{user_id}] Пользователь выбрал просмотр: {choice}")

    if choice == "show_alarms":
        if not bot_state.active_alarms:
            logger.warning(f"[{user_id}] Нет активных сбоев для отображения")
            await call.answer("⚠️ Нет активных сбоёв", show_alert=True)
            return

        alarm_text = "<b>🚨 Активные сбои:</b>\n\n"
        for alarm_id, alarm_info in bot_state.active_alarms.items():
            try:
                fix_time = alarm_info["fix_time"].strftime("%d.%m.%Y %H:%M")
            except Exception as e:
                logger.error(f"[{user_id}] Ошибка форматирования времени сбоя {alarm_id}: {e}")
                fix_time = "неизвестно"

            author = alarm_info.get("user_id", "Неизвестен")
            logger.debug(f"[{user_id}] Отображение сбоя: {alarm_id}, исправим до: {fix_time}, автор: {author}")
            alarm_text += f"• ID: <code>{alarm_id}</code>, исправим до {fix_time}, автор: {author}\n"

        try:
            await call.message.edit_text(alarm_text, parse_mode="HTML", reply_markup=create_refresh_keyboard())
        except Exception as e:
            logger.warning(f"[{user_id}] Ошибка при редактировании сообщения (сбои): {e}")
            await call.message.answer(alarm_text, parse_mode="HTML", reply_markup=create_refresh_keyboard())

        await call.answer()

    elif choice == "show_maintenances":
        if not bot_state.active_maintenances:
            logger.warning(f"[{user_id}] Нет активных работ для отображения")
            await call.answer("⚠️ Нет активных работ", show_alert=True)
            return

        maint_text = "<b>🔧 Активные работы:</b>\n\n"
        for work_id, work_info in bot_state.active_maintenances.items():
            try:
                start_time = work_info["start_time"].strftime("%d.%m.%Y %H:%M")
                end_time = work_info["end_time"].strftime("%d.%m.%Y %H:%M")
            except Exception as e:
                logger.error(f"[{user_id}] Ошибка форматирования времени работы {work_id}: {e}")
                start_time = end_time = "неизвестно"

            maint_text += f"• ID: <code>{work_id}</code>, начало: {start_time}, окончание: {end_time}\n"
            logger.debug(f"[{user_id}] Отображение работы: {work_id}, начало: {start_time}, окончание: {end_time}")

        try:
            await call.message.edit_text(maint_text, parse_mode="HTML", reply_markup=create_refresh_keyboard())
        except Exception as e:
            logger.warning(f"[{user_id}] Ошибка при редактировании сообщения (работы): {e}")
            await call.message.answer(maint_text, parse_mode="HTML", reply_markup=create_refresh_keyboard())

        await call.answer()
    else:
        logger.warning(f"[{user_id}] Неизвестный callback: {choice}")
        await call.answer("❌ Неизвестная команда", show_alert=True)


@router.callback_query(F.data == "refresh_selection")
async def refresh_selection(call: CallbackQuery):
    user_id = call.from_user.id
    logger.info(f"[{user_id}] Пользователь нажал «🔄 Обновить»")
    await call.answer("🔄 Обновляю список...", show_alert=False)

    # Повторный вызов начального меню
    await show_current_events(call.message)
    logger.info(f"[{user_id}] Список событий обновлён")
    await call.answer()


@router.callback_query(F.data == "close_selection")
async def close_selection(call: CallbackQuery):
    user_id = call.from_user.id
    logger.info(f"[{user_id}] Пользователь нажал «❌ Закрыть»")

    try:
        await call.message.delete()
        logger.debug(f"[{user_id}] Сообщение удалено успешно")
    except Exception as e:
        logger.warning(f"[{user_id}] Ошибка удаления сообщения: {e}")

    await call.answer("🚫 Меню закрыто")

