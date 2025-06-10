import asyncio
import sys
import os

# Добавляем корневую директорию проекта в sys.path
# Это позволяет импортировать модули, такие как 'common'
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from common.jira.client import JiraApiClient
from common.jira.config import JiraConfig


async def main():
    try:
        # Инициализация конфигурации и клиента
        config = JiraConfig()
        async with JiraApiClient(config) as client:
            # Получение списка типов задач
            print("\nДоступные типы задач:")
            issue_types = await client.get_issue_types()
            for issue_type in issue_types:
                print(f"- {issue_type['name']} (ID: {issue_type['id']})")
            
            # Получение метаданных для создания задачи в проекте HD с полями
            print("\nМетаданные для создания задачи в проекте HD (с полями):")
            create_meta = await client.get_create_issue_metadata(project_key="HD", expand="projects.issuetypes.fields")
            import json
            print(json.dumps(create_meta, indent=2, ensure_ascii=False))
            
            # Создание новой задачи
            issue_data = {
                "fields": {
                    "project": {
                        "key": "HD"
                    },
                    "summary": "Тестовая задача",
                    "description": "Это тестовая задача, созданная через API",
                    "issuetype": {
                        "id": "10201"  # ID типа "Service Request" для проекта HD
                    },
                    "assignee": {
                        "name": "sa.duty"  # Используем существующего пользователя
                    }
                }
            }
            
            new_issue = await client.create_issue(issue_data)
            print(f"\nСоздана новая задача: {new_issue.key}")
            
            # Добавление комментария
            comment = await client.add_comment(new_issue.key, "Тестовый комментарий")
            print(f"Добавлен комментарий: {comment['id']}")
            
            # Переход задачи
            transitions = await client.get_transitions(new_issue.key)
            if transitions:
                transition_id = transitions[0].id
                await client.transition_issue(new_issue.key, transition_id)
                print(f"Задача переведена в статус: {transitions[0].name}")
            
            # Поиск задач
            jql = f'project = HD AND assignee = sa.duty ORDER BY created DESC'
            issues = await client.search_issues(jql)
            print("\nНайденные задачи:")
            for issue in issues:
                print(f"- {issue.key}: {issue.summary}")
                
    except Exception as e:
        print(f"Ошибка: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 