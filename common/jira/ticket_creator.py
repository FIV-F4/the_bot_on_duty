"""
Функции для создания заявок в JIRA.
"""
import asyncio
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import requests

# Внимание: относительные импорты здесь не работают, если файл запускается напрямую.
# Если вы запускаете этот файл напрямую, убедитесь, что PYTHONPATH настроен корректно.
# Для запуска из корневой директории проекта можно использовать: python -m common.jira.ticket_creator
from common.jira.client import JiraApiClient
from common.jira.config import JiraConfig # Импортируем JiraConfig

# Внимание: относительные импорты здесь не работают, если файл запускается напрямую.
# Все импорты JiraApiClient, JiraConfig и JiraError будут выполнены внутри main().


async def create_technical_issue(
    client: JiraApiClient,
    employee_name: str,
    manager_name: str,
    description: str = "",
    date: str = "",
    start_time: str = "",
    problem_side: str = ""
) -> dict:
    """Создает заявку о технической неполадке в JIRA Service Desk."""
    project_key = "SCHED"
    issue_type_id = "10408"  # ID для 'Сервисный запрос'

    # Исполнитель берется из шаблона SCHED-143313
    assignee_name = "firstline.ws@petrovich.ru"

    description = f"""
Сотрудник: {employee_name}
Руководитель: {manager_name}
Описание: {description}
    """.strip()

    fields = {
        "project": {"key": project_key},
        "issuetype": {"id": issue_type_id},
        "summary": "Тех. неполадка",
        "description": description,
        "assignee": {"name": assignee_name},
        "labels": ["чатбот"],
        "priority": {"id": "3"}
    }

    # Добавляем кастомные поля если они предоставлены
    if date:
        fields["customfield_17429"] = date  # Дата
    
    if start_time:
        fields["customfield_17430"] = start_time  # Время начала
    
    if problem_side:
        # Преобразуем текстовое описание в ID значения
        if "оператора" in problem_side.lower():
            fields["customfield_17432"] = {"id": "18046"}  # Проблема на стороне оператора
        elif "компании" in problem_side.lower():
            fields["customfield_17432"] = {"id": "18047"}  # Проблема со стороны компании

    return await client.create_issue({"fields": fields})


async def create_sick_leave(
    client: JiraApiClient,
    employee_name: str,
    manager_name: str,
    description: str = "",
    open_date: str = "",
    for_who: str = ""
) -> dict:
    """Создает заявку о больничном в JIRA Service Desk."""
    project_key = "SCHED"
    issue_type_id = "10408"  # ID для 'Сервисный запрос'

    # Исполнитель берется из шаблона SCHED-143316
    assignee_name = "firstline.ws@petrovich.ru"

    description = f"""
Сотрудник: {employee_name}
Руководитель: {manager_name}
Описание: {description}
    """.strip()

    fields = {
        "project": {"key": project_key},
        "issuetype": {"id": issue_type_id},
        "summary": "Больничный",
        "description": description,
        "assignee": {"name": assignee_name},
        "labels": ["чатбот"],
        "priority": {"id": "3"}
    }

    # Добавляем обязательные кастомные поля
    if open_date:
        fields["customfield_17429"] = open_date  # Дата открытия
    
    if for_who:
        # Преобразуем текстовое описание в ID значения
        if "уход" in for_who.lower():
            fields["customfield_16004"] = {"id": "18027"}  # По уходу за больным
        elif "себя" in for_who.lower():
            fields["customfield_16004"] = {"id": "18028"}  # На себя

    return await client.create_issue({"fields": fields})


async def get_issue_details(client: JiraApiClient, issue_key: str) -> dict:
    """Получает полную информацию о задаче."""
    print(f"\nПолучение информации о задаче {issue_key}...")
    issue = await client.get_issue(issue_key)
    print("\nПолная информация о задаче:")
    print(json.dumps(issue, indent=2, ensure_ascii=False))
    return issue


def create_sd_request(
    jira_url: str,
    api_token: str,
    service_desk_id: str,
    request_type_id: str,
    summary: str,
    description: str,
    assignee: str
) -> dict:
    """
    Создает заявку через JIRA Service Desk API.
    
    Args:
        jira_url: URL JIRA (например, https://jira.petrovich.tech)
        api_token: API токен
        service_desk_id: ID сервис-деска (например, "55")
        request_type_id: ID типа запроса (например, "926" для больничного)
        summary: Заголовок заявки
        description: Описание заявки
        assignee: Имя исполнителя (например, "firstline.ws@petrovich.ru")
    
    Returns:
        dict: Ответ от JIRA Service Desk API
    """
    print(f"Создаем заявку через Service Desk API на {jira_url}/rest/servicedeskapi/request")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Atlassian-Token": "no-check"
    }
    payload = {
        "serviceDeskId": service_desk_id,
        "requestTypeId": request_type_id,
        "requestFieldValues": {
            "summary": summary,
            "description": description,
            "assignee": assignee
        }
    }
    response = requests.post(
        f"{jira_url}/rest/servicedeskapi/request",
        headers=headers,
        json=payload,
        auth=("", api_token)  # Изменено для использования пустого логина и токена как пароля
    )
    response.raise_for_status()
    return response.json()


async def main():
    """Основная функция для выполнения операций JIRA."""
    load_dotenv()
    jira_url = os.getenv("JIRA_URL")
    api_token = os.getenv("JIRA_API_TOKEN")

    if not jira_url or not api_token:
        print("Пожалуйста, установите переменные окружения JIRA_URL и JIRA_API_TOKEN.")
        return

    # Создаем объект конфигурации JIRA
    config = JiraConfig(
        JIRA_URL=jira_url,
        JIRA_API_TOKEN=api_token,
        JIRA_DEFAULT_PROJECT="SCHED"
    )
    client = JiraApiClient(config=config)

    try:
        async with client:
            # Получаем информацию о конкретной задаче SCHED-143316
            print("\n=== Получение информации о задаче SCHED-143316 ===")
            issue = await client.get_issue("SCHED-143316")
            
            print("\nСохранение информации о задаче в файл...")
            # Преобразуем объект в словарь
            issue_dict = issue.dict() if hasattr(issue, 'dict') else issue.__dict__
            def default_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return str(obj)
            with open('sched_143316.json', 'w', encoding='utf-8') as f:
                json.dump(issue_dict, f, ensure_ascii=False, indent=2, default=default_serializer)
            print('sched_143316.json сохранён!')

    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    # Загружаем переменные окружения
    load_dotenv()
    
    # Создаем конфигурацию
    config = JiraConfig(
        JIRA_URL=os.getenv("JIRA_URL"),
        JIRA_API_TOKEN=os.getenv("JIRA_API_TOKEN"),
        JIRA_DEFAULT_PROJECT="SCHED"
    )
    
    async def test_create_tickets():
        try:
            # Тестируем создание заявки через Service Desk API
            print("\nТестирование создания заявки через Service Desk API...")
            sd_response = create_sd_request(
                jira_url=os.getenv("JIRA_URL"),
                api_token=os.getenv("JIRA_API_TOKEN"),
                service_desk_id="55",
                request_type_id="926",  # для больничного
                summary="Тестовая заявка через Service Desk API",
                description="Описание тестовой заявки",
                assignee="firstline.ws@petrovich.ru"
            )
            print("Ответ от Service Desk API:", sd_response)
        except Exception as e:
            print(f"Ошибка при создании заявок: {e}")
    
    # Запускаем тест
    asyncio.run(test_create_tickets())