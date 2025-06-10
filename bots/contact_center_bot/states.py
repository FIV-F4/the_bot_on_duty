"""
Состояния для бота контакт-центра.
"""
from aiogram.fsm.state import State, StatesGroup

class TechnicalIssueStates(StatesGroup):
    """Состояния для создания заявки о технической неполадке."""
    ENTER_EMPLOYEE_NAME = State()  # Ввод имени сотрудника
    ENTER_MANAGER_NAME = State()   # Ввод имени руководителя
    ENTER_DESCRIPTION = State()    # Ввод описания проблемы

class SickLeaveStates(StatesGroup):
    """Состояния для создания заявки о больничном."""
    ENTER_EMPLOYEE_NAME = State()  # Ввод имени сотрудника
    ENTER_MANAGER_NAME = State()   # Ввод имени руководителя
    ENTER_DESCRIPTION = State()    # Ввод описания 