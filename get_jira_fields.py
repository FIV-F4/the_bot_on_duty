#!/usr/bin/env python3
"""
Скрипт для получения информации о всех полях JIRA и их возможных значениях.

Использование:
    python get_jira_fields.py                           # Все поля для SCHED / Сервисный запрос
    python get_jira_fields.py PROJ-KEY                  # Все поля для указанного проекта
    python get_jira_fields.py PROJ-KEY 10408            # Все поля для проекта и типа задачи
    python get_jira_fields.py field customfield_10001   # Информация о конкретном поле
    
Примеры:
    python get_jira_fields.py
    python get_jira_fields.py SCHED 10408
    python get_jira_fields.py field summary
    python get_jira_fields.py field customfield_10001 SCHED 10408
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common.jira.info_viewer import get_all_jira_fields_info, view_specific_field_info
from common.jira.config import JiraConfig

def print_usage():
    """Выводит справку по использованию скрипта."""
    print(__doc__)

async def main():
    """Основная функция скрипта."""
    
    if len(sys.argv) == 1:
        # Без аргументов - показываем все поля для SCHED / Сервисный запрос
        print("🔍 Получение всех полей для проекта SCHED, тип 'Сервисный запрос' (10408)")
        await get_all_jira_fields_info(project_key="SCHED", issue_type_id="10408")
        
    elif len(sys.argv) == 2:
        arg1 = sys.argv[1]
        
        if arg1 in ["-h", "--help", "help"]:
            print_usage()
            return
            
        # Один аргумент - ключ проекта
        print(f"🔍 Получение всех полей для проекта {arg1}")
        await get_all_jira_fields_info(project_key=arg1)
        
    elif len(sys.argv) == 3:
        arg1, arg2 = sys.argv[1], sys.argv[2]
        
        if arg1 == "field":
            # Информация о конкретном поле
            print(f"🔍 Получение информации о поле '{arg2}'")
            await view_specific_field_info(field_id=arg2)
        else:
            # Проект + тип задачи
            print(f"🔍 Получение всех полей для проекта {arg1}, тип задачи {arg2}")
            await get_all_jira_fields_info(project_key=arg1, issue_type_id=arg2)
            
    elif len(sys.argv) == 4:
        arg1, arg2, arg3 = sys.argv[1], sys.argv[2], sys.argv[3]
        
        if arg1 == "field":
            # Поле + проект
            print(f"🔍 Получение информации о поле '{arg2}' в проекте {arg3}")
            await view_specific_field_info(field_id=arg2, project_key=arg3)
        else:
            print("❌ Неверные аргументы")
            print_usage()
            
    elif len(sys.argv) == 5:
        arg1, arg2, arg3, arg4 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
        
        if arg1 == "field":
            # Поле + проект + тип задачи
            print(f"🔍 Получение информации о поле '{arg2}' в проекте {arg3}, тип задачи {arg4}")
            await view_specific_field_info(field_id=arg2, project_key=arg3, issue_type_id=arg4)
        else:
            print("❌ Неверные аргументы")
            print_usage()
    else:
        print("❌ Слишком много аргументов")
        print_usage()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1) 