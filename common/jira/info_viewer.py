import asyncio
from typing import List, Dict, Any
from .config import JiraConfig
from .client import JiraApiClient
from .exceptions import JiraError
import json

async def view_jira_info():
    """Просматривает информацию о проектах JIRA и метаданных полей."""
    config = JiraConfig()
    async with JiraApiClient(config) as client:
        print("\n--- Все доступные проекты JIRA ---")
        try:
            projects = await client.get_all_projects()
            for project in projects:
                print(f"- {project['name']} (Key: {project['key']})")
        except JiraError as e:
            print(f"Ошибка при получении проектов: {e}")
            return

        print(f"\n--- Доступные типы задач для проекта '{config.JIRA_DEFAULT_PROJECT}' ---")
        try:
            issue_types = await client.get_issue_types()
            for issue_type in issue_types:
                print(f"- {issue_type['name']} (ID: {issue_type['id']})")
        except JiraError as e:
            print(f"Ошибка при получении типов задач: {e}")
            return

        print(f"\n--- Обязательные поля для создания задачи (Ошибка) в проекте '{config.JIRA_DEFAULT_PROJECT}' ---")
        error_issue_type_id = None
        for issue_type in issue_types:
            if issue_type['name'].lower() == "ошибка":
                error_issue_type_id = issue_type['id']
                break

        if error_issue_type_id:
            try:
                metadata = await client.get_create_issue_metadata(
                    project_key=config.JIRA_DEFAULT_PROJECT,
                    issue_type_id=error_issue_type_id
                )
                print(f"[DEBUG] Полные метаданные createmeta: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
                projects_meta = metadata.get("projects", [])
                if projects_meta:
                    for project_meta in projects_meta:
                        if project_meta['key'] == config.JIRA_DEFAULT_PROJECT:
                            for issuetype_meta in project_meta.get("issuetypes", []):
                                if issuetype_meta['id'] == error_issue_type_id:
                                    print(f"Обязательные поля для '{issuetype_meta['name']}':")
                                    for field_name, field_info in issuetype_meta['fields'].items():
                                        if field_info.get("required"):
                                            print(f"- {field_name} (Имя: {field_info['name']})")
                                    break
                            break
                else:
                    print(f"Метаданные для проекта '{config.JIRA_DEFAULT_PROJECT}' не найдены.")
            except JiraError as e:
                print(f"Ошибка при получении метаданных: {e}")
        else:
            print("Тип задачи 'Ошибка' не найден.")

if __name__ == "__main__":
    asyncio.run(view_jira_info()) 