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

from bots.contact_center_bot.keyboards import create_main_keyboard
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

@router.message(F.text == "Тех. неполадка")
@admin_required(auth_enabled_for_bot=BOT_AUTH_ENABLED)
async def start_technical_issue(message: Message, state: FSMContext):
    """Начало создания заявки о технической неполадке."""
    await state.set_state(TechnicalIssueStates.ENTER_EMPLOYEE_NAME)
    await message.answer("Введите ФИО сотрудника:")

@router.message(TechnicalIssueStates.ENTER_EMPLOYEE_NAME)
async def enter_employee_name_tech(message: Message, state: FSMContext):
    """Обработка ввода имени сотрудника для технической неполадки."""
    await state.update_data(employee_name=message.text)
    await state.set_state(TechnicalIssueStates.ENTER_MANAGER_NAME)
    await message.answer("Введите ФИО руководителя:")

@router.message(TechnicalIssueStates.ENTER_MANAGER_NAME)
async def enter_manager_name_tech(message: Message, state: FSMContext):
    """Обработка ввода имени руководителя для технической неполадки."""
    await state.update_data(manager_name=message.text)
    await state.set_state(TechnicalIssueStates.ENTER_DESCRIPTION)
    await message.answer("Опишите проблему:")

@router.message(TechnicalIssueStates.ENTER_DESCRIPTION)
async def enter_description_tech(message: Message, state: FSMContext):
    """Обработка ввода описания и создание заявки о технической неполадке."""
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
            issue = await create_technical_issue(
                client=client,
                employee_name=data["employee_name"],
                manager_name=data["manager_name"],
                description=message.text
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

@router.message(F.text == "Больничный")
@admin_required(auth_enabled_for_bot=BOT_AUTH_ENABLED)
async def start_sick_leave(message: Message, state: FSMContext):
    """Начало создания заявки о больничном."""
    await state.set_state(SickLeaveStates.ENTER_EMPLOYEE_NAME)
    await message.answer("Введите ФИО сотрудника:")

@router.message(SickLeaveStates.ENTER_EMPLOYEE_NAME)
async def enter_employee_name_sick(message: Message, state: FSMContext):
    """Обработка ввода имени сотрудника для больничного."""
    await state.update_data(employee_name=message.text)
    await state.set_state(SickLeaveStates.ENTER_MANAGER_NAME)
    await message.answer("Введите ФИО руководителя:")

@router.message(SickLeaveStates.ENTER_MANAGER_NAME)
async def enter_manager_name_sick(message: Message, state: FSMContext):
    """Обработка ввода имени руководителя для больничного."""
    await state.update_data(manager_name=message.text)
    await state.set_state(SickLeaveStates.ENTER_DESCRIPTION)
    await message.answer("Введите описание больничного:")

@router.message(SickLeaveStates.ENTER_DESCRIPTION)
async def enter_description_sick(message: Message, state: FSMContext):
    """Обработка ввода описания и создание заявки о больничном."""
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
                description=message.text
            )
            
            jira_ticket_url = f"{config.JIRA_URL}/browse/{issue.get('key')}"
            await message.answer(
                f"✅ Заявка создана: <a href=\"{jira_ticket_url}\">{issue.get('key')}</a>\n"
                f"• Сотрудник: {data['employee_name']}\n"
                f"• Руководитель: {data['manager_name']}\n"
                f"• Описание: {message.text}",
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