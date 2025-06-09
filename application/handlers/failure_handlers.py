from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from application.services.failure_service import FailureService

router = Router()

class FailureStates(StatesGroup):
    """Состояния для создания сбоя"""
    waiting_for_title = State()
    waiting_for_description = State()

@router.message(Command("create_failure"))
async def cmd_create_failure(message: Message, state: FSMContext):
    """Обработчик команды создания сбоя"""
    await message.answer("Введите заголовок сбоя:")
    await state.set_state(FailureStates.waiting_for_title)

@router.message(FailureStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Обработчик ввода заголовка"""
    await state.update_data(title=message.text)
    await message.answer("Введите описание сбоя:")
    await state.set_state(FailureStates.waiting_for_description)

@router.message(FailureStates.waiting_for_description)
async def process_description(
    message: Message,
    state: FSMContext,
    failure_service: FailureService
):
    """Обработчик ввода описания"""
    data = await state.get_data()
    title = data["title"]
    description = message.text
    
    # Создаем сбой
    failure = await failure_service.create_failure(
        title=title,
        description=description,
        created_by=message.from_user.full_name
    )
    
    await message.answer(
        f"Сбой создан!\n"
        f"ID: {failure.id}\n"
        f"Заголовок: {failure.title}"
    )
    
    await state.clear()

@router.message(Command("extend_failure"))
async def cmd_extend_failure(message: Message):
    """Обработчик команды продления сбоя"""
    try:
        failure_id = int(message.text.split()[1])
        failure = await failure_service.extend_failure(
            failure_id=failure_id,
            extended_by=message.from_user.full_name
        )
        
        if failure:
            await message.answer(
                f"Сбой продлен!\n"
                f"ID: {failure.id}\n"
                f"Заголовок: {failure.title}"
            )
        else:
            await message.answer("Сбой не найден")
            
    except (IndexError, ValueError):
        await message.answer(
            "Использование: /extend_failure <ID>\n"
            "Пример: /extend_failure 1"
        )

@router.message(Command("resolve_failure"))
async def cmd_resolve_failure(message: Message):
    """Обработчик команды разрешения сбоя"""
    try:
        failure_id = int(message.text.split()[1])
        failure = await failure_service.resolve_failure(failure_id)
        
        if failure:
            await message.answer(
                f"Сбой разрешен!\n"
                f"ID: {failure.id}\n"
                f"Заголовок: {failure.title}"
            )
        else:
            await message.answer("Сбой не найден")
            
    except (IndexError, ValueError):
        await message.answer(
            "Использование: /resolve_failure <ID>\n"
            "Пример: /resolve_failure 1"
        )

@router.message(Command("list_failures"))
async def cmd_list_failures(message: Message):
    """Обработчик команды списка сбоев"""
    failures = await failure_service.get_active_failures()
    
    if not failures:
        await message.answer("Активных сбоев нет")
        return
        
    text = "Активные сбои:\n\n"
    for failure in failures:
        text += (
            f"ID: {failure.id}\n"
            f"Заголовок: {failure.title}\n"
            f"Создан: {failure.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Создал: {failure.created_by}\n\n"
        )
    
    await message.answer(text) 