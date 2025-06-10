"""
Скрипт для ручного тестирования создания заявок в JIRA.
"""
import asyncio
import os
from dotenv import load_dotenv

from common.jira.config import JiraConfig
from common.jira.client import JiraApiClient
from common.jira.ticket_creator import create_technical_issue, create_sick_leave

async def test_create_tickets():
    """Тестирование создания заявок в JIRA."""
    try:
        # Создаем клиент JIRA
        config = JiraConfig(
            JIRA_URL=os.getenv("JIRA_URL"),
            JIRA_API_TOKEN=os.getenv("JIRA_API_TOKEN"),
            JIRA_DEFAULT_PROJECT="SCHED"
        )
        
        async with JiraApiClient(config) as client:
            # Тестируем создание заявки о технической неполадке
            print("\n=== Тестирование создания заявки о технической неполадке ===")
            tech_issue = await create_technical_issue(
                client=client,
                employee_name="Тестовый Сотрудник",
                manager_name="Тестовый Руководитель",
                description="Тестовое описание технической неполадки"
            )
            print(f"✅ Создана заявка о технической неполадке: {tech_issue.get('key')}")
            
            # Тестируем создание заявки о больничном
            print("\n=== Тестирование создания заявки о больничном ===")
            sick_issue = await create_sick_leave(
                client=client,
                employee_name="Тестовый Сотрудник",
                manager_name="Тестовый Руководитель",
                description="Тестовое описание больничного"
            )
            print(f"✅ Создана заявка о больничном: {sick_issue.get('key')}")
            
    except Exception as e:
        print(f"❌ Ошибка при создании заявок: {e}")

if __name__ == "__main__":
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем наличие необходимых переменных
    if not os.getenv("JIRA_URL") or not os.getenv("JIRA_API_TOKEN"):
        print("❌ Ошибка: Не найдены переменные окружения JIRA_URL или JIRA_API_TOKEN")
        exit(1)
    
    # Запускаем тесты
    asyncio.run(test_create_tickets()) 