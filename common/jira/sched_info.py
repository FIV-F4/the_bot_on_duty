"""
Скрипт для просмотра информации о полях проекта SCHED в JIRA.
"""
import asyncio
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
from common.jira.config import JiraConfig
from common.jira.client import JiraApiClient
from common.jira.exceptions import JiraError
import json

async def view_sched_info():
    """Просматривает информацию о полях проекта SCHED в JIRA."""
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
        print("\n=== ИНФОРМАЦИЯ О ПРОЕКТЕ SCHED ===")
        
        # Получаем все проекты
        print("\n--- Все доступные проекты JIRA ---")
        try:
            projects = await client.get_all_projects()
            for project in projects:
                if project['key'] == 'SCHED':
                    print(f"✅ {project['name']} (Key: {project['key']}) - НАЙДЕН")
                else:
                    print(f"- {project['name']} (Key: {project['key']})")
        except JiraError as e:
            print(f"❌ Ошибка при получении проектов: {e}")
            return

        # Получаем типы задач
        print(f"\n--- Доступные типы задач ---")
        try:
            issue_types = await client.get_issue_types()
            service_request_found = False
            for issue_type in issue_types:
                if issue_type['id'] == '10408':
                    print(f"✅ {issue_type['name']} (ID: {issue_type['id']}) - СЕРВИСНЫЙ ЗАПРОС")
                    service_request_found = True
                else:
                    print(f"- {issue_type['name']} (ID: {issue_type['id']})")
            
            if not service_request_found:
                print("❌ Тип задачи с ID '10408' не найден!")
        except JiraError as e:
            print(f"❌ Ошибка при получении типов задач: {e}")
            return

        # Получаем метаданные для создания задачи
        print(f"\n--- ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ДЛЯ 'СЕРВИСНЫЙ ЗАПРОС' В ПРОЕКТЕ SCHED ---")
        service_request_issue_type_id = "10408"

        try:
            metadata = await client.get_create_issue_metadata(
                project_key="SCHED",
                issue_type_id=service_request_issue_type_id
            )
            
            # Сохраняем полные метаданные в файл для анализа
            print(f"\n💾 Сохранение полных метаданных в файл 'sched_metadata.json'...")
            with open('sched_metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            print("✅ Метаданные сохранены в файл 'sched_metadata.json'")
            
            print(f"\n[DEBUG] Структура метаданных:")
            print(f"Ключи верхнего уровня: {list(metadata.keys())}")
            
            projects_meta = metadata.get("projects", [])
            if projects_meta:
                print(f"Найдено проектов в метаданных: {len(projects_meta)}")
                
                for project_meta in projects_meta:
                    if project_meta['key'] == "SCHED":
                        print(f"\n✅ Найден проект SCHED в метаданных")
                        print(f"Ключи проекта: {list(project_meta.keys())}")
                        
                        issuetypes = project_meta.get("issuetypes", [])
                        print(f"Найдено типов задач: {len(issuetypes)}")
                        
                        for issuetype_meta in issuetypes:
                            if issuetype_meta['id'] == service_request_issue_type_id:
                                print(f"\n📋 Тип задачи: {issuetype_meta['name']}")
                                print(f"🔧 ID: {issuetype_meta['id']}")
                                print(f"Ключи типа задачи: {list(issuetype_meta.keys())}")
                                
                                # Проверяем наличие поля 'fields'
                                if 'fields' in issuetype_meta:
                                    fields = issuetype_meta['fields']
                                    print(f"Найдено полей: {len(fields)}")
                                    
                                    # Обязательные поля
                                    print(f"\n🔴 ОБЯЗАТЕЛЬНЫЕ ПОЛЯ:")
                                    required_fields = []
                                    for field_name, field_info in fields.items():
                                        if field_info.get("required"):
                                            required_fields.append((field_name, field_info))
                                            print(f"  • {field_name}")
                                            print(f"    Название: {field_info['name']}")
                                            print(f"    Тип: {field_info.get('schema', {}).get('type', 'неизвестно')}")
                                            
                                            # Допустимые значения
                                            if 'allowedValues' in field_info:
                                                values = []
                                                for val in field_info['allowedValues']:
                                                    if isinstance(val, dict):
                                                        values.append(val.get('value', val.get('name', str(val))))
                                                    else:
                                                        values.append(str(val))
                                                print(f"    Допустимые значения: {values}")
                                            
                                            # Значение по умолчанию
                                            if 'defaultValue' in field_info:
                                                print(f"    Значение по умолчанию: {field_info['defaultValue']}")
                                            
                                            print()
                                    
                                    # Все поля
                                    print(f"\n📝 ВСЕ ПОЛЯ:")
                                    for field_name, field_info in fields.items():
                                        required = " 🔴" if field_info.get("required") else ""
                                        print(f"  • {field_name}{required}")
                                        print(f"    Название: {field_info['name']}")
                                        print(f"    Тип: {field_info.get('schema', {}).get('type', 'неизвестно')}")
                                        print()
                                else:
                                    print(f"❌ Поле 'fields' не найдено в метаданных типа задачи")
                                    print(f"Доступные поля: {list(issuetype_meta.keys())}")
                                
                                break
                        else:
                            print(f"❌ Тип задачи с ID '{service_request_issue_type_id}' не найден в проекте SCHED")
                        break
                else:
                    print(f"❌ Метаданные для проекта SCHED не найдены")
            else:
                print(f"❌ Метаданные не получены")
                
        except JiraError as e:
            print(f"❌ Ошибка при получении метаданных: {e}")
            print(f"Детали ошибки: {str(e)}")

if __name__ == "__main__":
    asyncio.run(view_sched_info()) 