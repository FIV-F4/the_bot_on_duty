"""
Состояния для бота контакт-центра.
"""
from aiogram.fsm.state import State, StatesGroup

class TechnicalIssueStates(StatesGroup):
    """Состояния для создания заявки о технической неполадке."""
    ENTER_EMPLOYEE_NAME = State()  # Ввод имени сотрудника
    ENTER_MANAGER_NAME = State()   # Ввод имени руководителя
    ENTER_DESCRIPTION = State()    # Ввод описания проблемы
    ENTER_DATE = State()           # Ввод даты
    ENTER_START_TIME = State()     # Ввод времени начала
    ENTER_PROBLEM_SIDE = State()   # Выбор стороны проблемы
    CONFIRMATION = State()         # Подтверждение данных

class SickLeaveStates(StatesGroup):
    """Состояния для создания заявки о больничном."""
    ENTER_EMPLOYEE_NAME = State()      # Ввод имени сотрудника
    ENTER_MANAGER_NAME = State()       # Ввод имени руководителя
    ENTER_OPEN_DATE = State()          # Ввод даты открытия
    ENTER_FOR_WHO = State()            # Выбор на кого открыт
    ENTER_DESCRIPTION = State()        # Ввод описания
    CONFIRMATION = State()             # Подтверждение данных 