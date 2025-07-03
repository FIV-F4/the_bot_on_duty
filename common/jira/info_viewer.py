import asyncio
from typing import List, Dict, Any, Optional
from .config import JiraConfig
from .client import JiraApiClient
from .exceptions import JiraError
import json
import os

async def get_all_jira_fields_info(project_key: str = None, issue_type_id: str = None):
    """
    Получает детальную информацию о всех полях JIRA для указанного проекта и типа задачи.
    
    Args:
        project_key: Ключ проекта (например, 'SCHED')
        issue_type_id: ID типа задачи (например, '10408' для 'Сервисный запрос')
    """
    config = JiraConfig()
    project_key = project_key or config.JIRA_DEFAULT_PROJECT
    
    async with JiraApiClient(config) as client:
        try:
            print(f"\n=== ПОЛУЧЕНИЕ ИНФОРМАЦИИ О ПОЛЯХ JIRA ===")
            print(f"Проект: {project_key}")
            print(f"Тип задачи ID: {issue_type_id or 'Все типы'}")
            print("=" * 60)
            
            # 1. Получаем все проекты
            print("\n1. Все доступные проекты:")
            projects = await client.get_all_projects()
            for project in projects:
                marker = " <-- ТЕКУЩИЙ" if project['key'] == project_key else ""
                print(f"   - {project['name']} (Key: {project['key']}){marker}")
            
            # 2. Получаем все типы задач
            print(f"\n2. Все типы задач:")
            issue_types = await client.get_issue_types()
            for issue_type in issue_types:
                marker = " <-- ВЫБРАННЫЙ" if str(issue_type['id']) == str(issue_type_id) else ""
                print(f"   - {issue_type['name']} (ID: {issue_type['id']}){marker}")
            
            # 3. Получаем метаданные для создания задач
            print(f"\n3. Метаданные полей для проекта '{project_key}':")
            
            # Получаем расширенные метаданные
            expand_params = "projects.issuetypes.fields"
            metadata = await client.get_create_issue_metadata(
                project_key=project_key,
                issue_type_id=issue_type_id,
                expand=expand_params
            )
            
            if not metadata.get("projects"):
                print(f"❌ Метаданные для проекта '{project_key}' не найдены.")
                return
            
            # Обрабатываем каждый проект
            for project_meta in metadata["projects"]:
                if project_meta['key'] != project_key:
                    continue
                    
                print(f"\n   Проект: {project_meta['name']} ({project_meta['key']})")
                
                # Обрабатываем каждый тип задачи
                for issuetype_meta in project_meta.get("issuetypes", []):
                    type_marker = " <-- ВЫБРАННЫЙ ТИП" if str(issuetype_meta['id']) == str(issue_type_id) else ""
                    print(f"\n   Тип задачи: {issuetype_meta['name']} (ID: {issuetype_meta['id']}){type_marker}")
                    
                    fields = issuetype_meta.get('fields', {})
                    if not fields:
                        print("     ❌ Поля не найдены для этого типа задачи.")
                        continue
                    
                    print(f"     Всего полей: {len(fields)}")
                    print("     " + "=" * 50)
                    
                    # Группируем поля по обязательности
                    required_fields = {}
                    optional_fields = {}
                    
                    for field_id, field_info in fields.items():
                        if field_info.get("required", False):
                            required_fields[field_id] = field_info
                        else:
                            optional_fields[field_id] = field_info
                    
                    # Показываем обязательные поля
                    print(f"\n     📋 ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ({len(required_fields)}):")
                    for field_id, field_info in required_fields.items():
                        await _print_field_info(field_id, field_info, indent="       ")
                    
                    # Показываем необязательные поля (только первые 10 для краткости)
                    print(f"\n     📝 НЕОБЯЗАТЕЛЬНЫЕ ПОЛЯ (показаны первые 10 из {len(optional_fields)}):")
                    for i, (field_id, field_info) in enumerate(optional_fields.items()):
                        if i >= 10:
                            print(f"       ... и еще {len(optional_fields) - 10} полей")
                            break
                        await _print_field_info(field_id, field_info, indent="       ")
                    
                    # Сохраняем полную информацию в файл
                    await _save_fields_to_file(project_key, issuetype_meta['name'], fields)
                    
        except JiraError as e:
            print(f"❌ Ошибка при получении информации: {e}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")

async def _print_field_info(field_id: str, field_info: Dict[str, Any], indent: str = ""):
    """Выводит информацию о поле в читаемом формате."""
    name = field_info.get('name', 'Без названия')
    field_type = field_info.get('schema', {}).get('type', 'unknown')
    required = "🔴 ОБЯЗАТЕЛЬНО" if field_info.get('required') else "⚪ Необязательно"
    
    print(f"{indent}• {name} (ID: {field_id})")
    print(f"{indent}  Тип: {field_type} | {required}")
    
    # Показываем возможные значения
    allowed_values = field_info.get('allowedValues')
    if allowed_values:
        print(f"{indent}  Возможные значения:")
        for value in allowed_values[:5]:  # Показываем только первые 5
            value_name = value.get('name', value.get('value', str(value)))
            value_id = value.get('id', '')
            print(f"{indent}    - {value_name} (ID: {value_id})")
        if len(allowed_values) > 5:
            print(f"{indent}    ... и еще {len(allowed_values) - 5} значений")
    
    # Показываем значение по умолчанию
    default_value = field_info.get('defaultValue')
    if default_value:
        default_name = default_value.get('name', default_value.get('value', str(default_value)))
        print(f"{indent}  По умолчанию: {default_name}")
    
    print()

async def _save_fields_to_file(project_key: str, issue_type_name: str, fields: Dict[str, Any]):
    """Сохраняет полную информацию о полях в JSON файл."""
    filename = f"jira_fields_{project_key}_{issue_type_name.replace(' ', '_')}.json"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(fields, f, indent=2, ensure_ascii=False)
        print(f"     💾 Полная информация о полях сохранена в: {filename}")
    except Exception as e:
        print(f"     ❌ Ошибка при сохранении файла: {e}")

async def view_jira_info():
    """Просматривает информацию о проектах JIRA и метаданных полей."""
    # Получаем информацию для проекта SCHED и типа "Сервисный запрос"
    await get_all_jira_fields_info(project_key="SCHED", issue_type_id="10408")

async def view_specific_field_info(field_id: str, project_key: str = "SCHED", issue_type_id: str = "10408"):
    """Получает детальную информацию о конкретном поле."""
    config = JiraConfig()
    
    async with JiraApiClient(config) as client:
        try:
            metadata = await client.get_create_issue_metadata(
                project_key=project_key,
                issue_type_id=issue_type_id,
                expand="projects.issuetypes.fields"
            )
            
            for project_meta in metadata.get("projects", []):
                if project_meta['key'] != project_key:
                    continue
                    
                for issuetype_meta in project_meta.get("issuetypes", []):
                    if str(issuetype_meta['id']) != str(issue_type_id):
                        continue
                    
                    fields = issuetype_meta.get('fields', {})
                    field_info = fields.get(field_id)
                    
                    if field_info:
                        print(f"\n=== ИНФОРМАЦИЯ О ПОЛЕ {field_id} ===")
                        await _print_field_info(field_id, field_info)
                        
                        # Показываем полную JSON структуру
                        print("Полная JSON структура:")
                        print(json.dumps(field_info, indent=2, ensure_ascii=False))
                    else:
                        print(f"❌ Поле '{field_id}' не найдено")
                        
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Если передан аргумент - показываем информацию о конкретном поле
        field_id = sys.argv[1]
        project_key = sys.argv[2] if len(sys.argv) > 2 else "SCHED"
        issue_type_id = sys.argv[3] if len(sys.argv) > 3 else "10408"
        
        print(f"Получение информации о поле: {field_id}")
        asyncio.run(view_specific_field_info(field_id, project_key, issue_type_id))
    else:
        # Показываем общую информацию
        asyncio.run(view_jira_info()) 