"""
Скрипт для тестирования создания заявки в проекте SCHED и определения обязательных полей.
"""
import asyncio
import os
from dotenv import load_dotenv
from common.jira.config import JiraConfig
from common.jira.client import JiraApiClient
from common.jira.exceptions import JiraError
import json

async def test_sched_creation():
    """Тестирует создание заявки в SCHED для определения обязательных полей."""
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем наличие необходимых переменных
    if not os.getenv("JIRA_URL") or not os.getenv("JIRA_API_TOKEN"):
        print("❌ Ошибка: Не найдены переменные окружения JIRA_URL или JIRA_API_TOKEN")
        return
    
    config = JiraConfig(
        JIRA_URL=os.getenv("JIRA_URL"),
        JIRA_API_TOKEN=os.getenv("JIRA_API_TOKEN"),
        JIRA_DEFAULT_PROJECT="SCHED"
    )
    
    async with JiraApiClient(config) as client:
        print("\n=== ТЕСТИРОВАНИЕ СОЗДАНИЯ ЗАЯВКИ В SCHED ===")
        
        # Тест 1: Минимальные поля
        print("\n--- Тест 1: Минимальные поля ---")
        try:
            minimal_data = {
                "fields": {
                    "project": {"key": "SCHED"},
                    "issuetype": {"id": "10408"},
                    "summary": "Тестовая заявка - минимальные поля"
                }
            }
            
            print("Отправляем данные:")
            print(json.dumps(minimal_data, indent=2, ensure_ascii=False))
            
            result = await client.create_issue(minimal_data)
            print(f"✅ Успешно создана заявка: {result.get('key')}")
            
            # Удаляем тестовую заявку
            print("🗑️ Удаляем тестовую заявку...")
            # Здесь можно добавить удаление заявки, если нужно
            
        except JiraError as e:
            print(f"❌ Ошибка при создании с минимальными полями: {e}")
            
            # Анализируем ошибку для определения обязательных полей
            error_text = str(e)
            if "required" in error_text.lower():
                print("\n🔍 Анализ ошибки - найдены обязательные поля:")
                # Извлекаем информацию об обязательных полях из ошибки
                print(error_text)
        
        # Тест 2: С полным описанием
        print("\n--- Тест 2: С полным описанием ---")
        try:
            full_data = {
                "fields": {
                    "project": {"key": "SCHED"},
                    "issuetype": {"id": "10408"},
                    "summary": "Тестовая заявка - полные поля",
                    "description": "Это тестовое описание заявки для проверки полей"
                }
            }
            
            print("Отправляем данные:")
            print(json.dumps(full_data, indent=2, ensure_ascii=False))
            
            result = await client.create_issue(full_data)
            print(f"✅ Успешно создана заявка: {result.get('key')}")
            
        except JiraError as e:
            print(f"❌ Ошибка при создании с полными полями: {e}")
        
        # Тест 3: С исполнителем
        print("\n--- Тест 3: С исполнителем ---")
        try:
            assignee_data = {
                "fields": {
                    "project": {"key": "SCHED"},
                    "issuetype": {"id": "10408"},
                    "summary": "Тестовая заявка - с исполнителем",
                    "description": "Тестовое описание",
                    "assignee": {"name": "firstline.ws@petrovich.ru"}
                }
            }
            
            print("Отправляем данные:")
            print(json.dumps(assignee_data, indent=2, ensure_ascii=False))
            
            result = await client.create_issue(assignee_data)
            print(f"✅ Успешно создана заявка: {result.get('key')}")
            
        except JiraError as e:
            print(f"❌ Ошибка при создании с исполнителем: {e}")
        
        # Тест 4: Попытка получить информацию о существующей заявке
        print("\n--- Тест 4: Анализ существующей заявки ---")
        try:
            # Пытаемся получить информацию о существующей заявке SCHED
            existing_issue = await client.get_issue("SCHED-143316")
            print(f"✅ Получена информация о заявке SCHED-143316")
            print(f"Поля заявки:")
            
            # Сохраняем информацию о заявке
            with open('sched_existing_issue.json', 'w', encoding='utf-8') as f:
                issue_data = existing_issue.dict() if hasattr(existing_issue, 'dict') else existing_issue.__dict__
                json.dump(issue_data, f, ensure_ascii=False, indent=2, default=str)
            print("💾 Информация о заявке сохранена в 'sched_existing_issue.json'")
            
        except JiraError as e:
            print(f"❌ Ошибка при получении информации о заявке: {e}")

if __name__ == "__main__":
    asyncio.run(test_sched_creation()) 