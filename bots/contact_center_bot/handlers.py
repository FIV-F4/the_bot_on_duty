"""
Обработчики команд для бота контакт-центра.
"""
import logging
import os
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from common.auth import admin_required
from common.jira.client import JiraApiClient
from common.jira.config import JiraConfig
from common.jira.ticket_creator import create_technical_issue, create_sick_leave

from bots.contact_center_bot.keyboards import (
    create_main_keyboard, 
    create_cancel_keyboard, 
    create_problem_side_keyboard, 
    create_confirm_keyboard,
    create_for_who_keyboard
)
from bots.contact_center_bot.states import TechnicalIssueStates, SickLeaveStates
from bots.contact_center_bot.config import AUTH_ENABLED as BOT_AUTH_ENABLED

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
@router.message(Command("help"))
async def start_command(message: Message):
    """Обработчик команд /start и /help."""
    await message.answer(
        "👋 Привет! Я бот для создания заявок в контакт-центре.\n"
        "Выберите тип заявки:",
        reply_markup=create_main_keyboard()
    )

@router.message(F.text == "🔧 Техническая неполадка")
@admin_required(auth_enabled_for_bot=BOT_AUTH_ENABLED)
async def start_technical_issue(message: Message, state: FSMContext):
    """Начало создания заявки о технической неполадке."""
    await state.set_state(TechnicalIssueStates.ENTER_EMPLOYEE_NAME)
    await message.answer(
        "🔧 Создание заявки о технической неполадке\n\n"
        "Введите ФИО сотрудника:",
        reply_markup=create_cancel_keyboard()
    )

@router.message(TechnicalIssueStates.ENTER_EMPLOYEE_NAME)
async def enter_employee_name_tech(message: Message, state: FSMContext):
    """Обработка ввода имени сотрудника для технической неполадки."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    
    await state.update_data(employee_name=message.text)
    await state.set_state(TechnicalIssueStates.ENTER_MANAGER_NAME)
    await message.answer(
        "Введите ФИО руководителя:",
        reply_markup=create_cancel_keyboard()
    )

@router.message(TechnicalIssueStates.ENTER_MANAGER_NAME)
async def enter_manager_name_tech(message: Message, state: FSMContext):
    """Обработка ввода имени руководителя для технической неполадки."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    
    await state.update_data(manager_name=message.text)
    await state.set_state(TechnicalIssueStates.ENTER_DESCRIPTION)
    await message.answer(
        "Опишите проблему:",
        reply_markup=create_cancel_keyboard()
    )

@router.message(TechnicalIssueStates.ENTER_DESCRIPTION)
async def enter_description_tech(message: Message, state: FSMContext):
    """Обработка ввода описания для технической неполадки."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    await state.update_data(description=message.text)
    await state.set_state(TechnicalIssueStates.ENTER_DATE)
    await message.answer(
        "Введите дату (формат: dd.mm.yyyy):",
        reply_markup=create_cancel_keyboard()
    )

@router.message(TechnicalIssueStates.ENTER_DATE)
async def enter_date_tech(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    try:
        parsed_date = datetime.strptime(message.text, "%d.%m.%Y")
        jira_date = parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Используйте формат dd.mm.yyyy (например: 17.06.2025):",
            reply_markup=create_cancel_keyboard()
        )
        return
    await state.update_data(date=jira_date)
    await state.set_state(TechnicalIssueStates.ENTER_START_TIME)
    await message.answer(
        "Введите время начала (формат: HH:MM):",
        reply_markup=create_cancel_keyboard()
    )

@router.message(TechnicalIssueStates.ENTER_START_TIME)
async def enter_start_time_tech(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    try:
        parsed_time = datetime.strptime(message.text, "%H:%M")
        jira_time = parsed_time.strftime("%H:%M")
    except ValueError:
        await message.answer(
            "❌ Неверный формат времени. Используйте формат HH:MM (например: 14:30):",
            reply_markup=create_cancel_keyboard()
        )
        return
    await state.update_data(start_time=jira_time)
    await state.set_state(TechnicalIssueStates.ENTER_PROBLEM_SIDE)
    await message.answer(
        "Выберите сторону проблемы:",
        reply_markup=create_problem_side_keyboard()
    )

@router.message(TechnicalIssueStates.ENTER_PROBLEM_SIDE)
async def enter_problem_side_tech(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    if message.text not in ["👤 Проблема на стороне оператора", "🏢 Проблема со стороны компании"]:
        await message.answer(
            "❌ Пожалуйста, выберите один из предложенных вариантов:",
            reply_markup=create_problem_side_keyboard()
        )
        return
    await state.update_data(problem_side=message.text)
    await state.set_state(TechnicalIssueStates.CONFIRMATION)
    data = await state.get_data()
    summary = f"""
📋 <b>Сводка заявки о технической неполадке:</b>

👤 <b>Сотрудник:</b> {data['employee_name']}
👨‍💼 <b>Руководитель:</b> {data['manager_name']}
�� <b>Описание:</b> {data['description']}
📅 <b>Дата:</b> {data['date']}
⏰ <b>Время начала:</b> {data['start_time']}
🎯 <b>Сторона проблемы:</b> {data['problem_side']}

Подтвердите создание заявки:
    """
    await message.answer(summary, reply_markup=create_confirm_keyboard())

@router.message(TechnicalIssueStates.CONFIRMATION)
async def confirm_technical_issue(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    if message.text != "✅ Подтвердить":
        await message.answer(
            "❌ Пожалуйста, выберите один из предложенных вариантов:",
            reply_markup=create_confirm_keyboard()
        )
        return
    data = await state.get_data()
    try:
        config = JiraConfig(
            JIRA_URL=os.getenv("JIRA_URL"),
            JIRA_API_TOKEN=os.getenv("JIRA_API_TOKEN"),
            JIRA_DEFAULT_PROJECT="SCHED"
        )
        async with JiraApiClient(config) as client:
            issue = await create_technical_issue(
                client=client,
                employee_name=data["employee_name"],
                manager_name=data["manager_name"],
                description=data["description"],
                date=data["date"],
                start_time=data["start_time"],
                problem_side=data["problem_side"]
            )
            jira_ticket_url = f"{config.JIRA_URL}/browse/{issue.get('key')}"
            await message.answer(
                f"✅ Заявка создана: <a href=\"{jira_ticket_url}\">{issue.get('key')}</a>\n"
                f"• Сотрудник: {data['employee_name']}\n"
                f"• Руководитель: {data['manager_name']}",
                reply_markup=create_main_keyboard()
            )
    except Exception as e:
        logger.error(f"Ошибка при создании заявки: {e}")
        await message.answer(
            "❌ Произошла ошибка при создании заявки.\n"
            "Пожалуйста, попробуйте позже.",
            reply_markup=create_main_keyboard()
        )
    finally:
        await state.clear()

@router.message(F.text == "🏥 Больничный")
@admin_required(auth_enabled_for_bot=BOT_AUTH_ENABLED)
async def start_sick_leave(message: Message, state: FSMContext):
    """Начало создания заявки о больничном."""
    await state.set_state(SickLeaveStates.ENTER_EMPLOYEE_NAME)
    await message.answer(
        "🏥 Создание заявки о больничном\n\n"
        "Введите имя сотрудника:",
        reply_markup=create_cancel_keyboard()
    )

@router.message(SickLeaveStates.ENTER_EMPLOYEE_NAME)
async def enter_employee_name_sick(message: Message, state: FSMContext):
    """Обработка ввода имени сотрудника для больничного."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    
    await state.update_data(employee_name=message.text)
    await state.set_state(SickLeaveStates.ENTER_MANAGER_NAME)
    await message.answer(
        "Введите имя руководителя:",
        reply_markup=create_cancel_keyboard()
    )

@router.message(SickLeaveStates.ENTER_MANAGER_NAME)
async def enter_manager_name_sick(message: Message, state: FSMContext):
    """Обработка ввода имени руководителя для больничного."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    
    await state.update_data(manager_name=message.text)
    await state.set_state(SickLeaveStates.ENTER_OPEN_DATE)
    await message.answer(
        "Введите дату открытия больничного (формат: dd.mm.yyyy):",
        reply_markup=create_cancel_keyboard()
    )

@router.message(SickLeaveStates.ENTER_OPEN_DATE)
async def enter_open_date_sick(message: Message, state: FSMContext):
    """Обработка ввода даты открытия больничного."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    
    # Валидация даты в формате dd.mm.yyyy
    try:
        # Парсим дату в формате dd.mm.yyyy
        parsed_date = datetime.strptime(message.text, "%d.%m.%Y")
        # Преобразуем в формат YYYY-MM-DD для JIRA
        jira_date = parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Используйте формат dd.mm.yyyy (например: 17.06.2025):",
            reply_markup=create_cancel_keyboard()
        )
        return
    
    await state.update_data(open_date=jira_date)
    await state.set_state(SickLeaveStates.ENTER_FOR_WHO)
    await message.answer(
        "Выберите на кого открыт больничный:",
        reply_markup=create_for_who_keyboard()
    )

@router.message(SickLeaveStates.ENTER_FOR_WHO)
async def enter_for_who_sick(message: Message, state: FSMContext):
    """Обработка выбора на кого открыт больничный."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    
    if message.text not in ["👤 По уходу за больным", "🏥 На себя"]:
        await message.answer(
            "❌ Пожалуйста, выберите один из предложенных вариантов:",
            reply_markup=create_for_who_keyboard()
        )
        return
    
    await state.update_data(for_who=message.text)
    await state.set_state(SickLeaveStates.ENTER_DESCRIPTION)
    await message.answer(
        "Введите описание (комментарий):",
        reply_markup=create_cancel_keyboard()
    )

@router.message(SickLeaveStates.ENTER_DESCRIPTION)
async def enter_description_sick(message: Message, state: FSMContext):
    """Обработка ввода описания и создание заявки о больничном."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    
    await state.update_data(description=message.text)
    await state.set_state(SickLeaveStates.CONFIRMATION)
    
    # Показываем сводку данных для подтверждения
    data = await state.get_data()
    summary = f"""
📋 <b>Сводка заявки о больничном:</b>

👤 <b>Сотрудник:</b> {data['employee_name']}
👨‍💼 <b>Руководитель:</b> {data['manager_name']}
📅 <b>Дата открытия:</b> {data['open_date']}
🎯 <b>На кого открыт:</b> {data['for_who']}
📝 <b>Описание:</b> {data['description']}

Подтвердите создание заявки:
    """
    await message.answer(summary, reply_markup=create_confirm_keyboard())

@router.message(SickLeaveStates.CONFIRMATION)
async def confirm_sick_leave(message: Message, state: FSMContext):
    """Подтверждение и создание заявки о больничном."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание заявки отменено", reply_markup=create_main_keyboard())
        return
    
    if message.text != "✅ Подтвердить":
        await message.answer(
            "❌ Пожалуйста, выберите один из предложенных вариантов:",
            reply_markup=create_confirm_keyboard()
        )
        return
    
    data = await state.get_data()
    
    try:
        # Создаем клиент JIRA
        config = JiraConfig(
            JIRA_URL=os.getenv("JIRA_URL"),
            JIRA_API_TOKEN=os.getenv("JIRA_API_TOKEN"),
            JIRA_DEFAULT_PROJECT="SCHED"
        )
        
        async with JiraApiClient(config) as client:
            # Создаем заявку
            issue = await create_sick_leave(
                client=client,
                employee_name=data["employee_name"],
                manager_name=data["manager_name"],
                description=data["description"],
                open_date=data["open_date"],
                for_who=data["for_who"]
            )
            
            jira_ticket_url = f"{config.JIRA_URL}/browse/{issue.get('key')}"
            await message.answer(
                f"✅ Заявка создана: <a href=\"{jira_ticket_url}\">{issue.get('key')}</a>\n"
                f"• Сотрудник: {data['employee_name']}\n"
                f"• Руководитель: {data['manager_name']}\n"
                f"• Дата открытия: {data['open_date']}\n"
                f"• На кого открыт: {data['for_who']}",
                reply_markup=create_main_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Ошибка при создании заявки: {e}")
        await message.answer(
            "❌ Произошла ошибка при создании заявки.\n"
            "Пожалуйста, попробуйте позже.",
            reply_markup=create_main_keyboard()
        )
    
    finally:
        await state.clear() 