import requests
import json
import sys
from config import CONFIG
from datetime import datetime
from urllib.parse import urljoin

def check_config():
    """
    Проверка наличия и корректности конфигурации
    """
    if "JIRA" not in CONFIG:
        print("Ошибка: Отсутствует секция JIRA в конфигурации")
        return False
        
    required_vars = ["LOGIN_URL", "TOKEN"]
    missing_vars = [var for var in required_vars if var not in CONFIG["JIRA"] or not CONFIG["JIRA"][var]]
    
    if missing_vars:
        print("Ошибка: Отсутствуют необходимые переменные в конфигурации JIRA:")
        for var in missing_vars:
            print(f"- {var}")
        return False
    
    if not CONFIG["JIRA"]["LOGIN_URL"].strip().startswith(('http://', 'https://')):
        print(f"Ошибка: Некорректный URL Jira: {CONFIG['JIRA']['LOGIN_URL']}")
        return False
    
    return True

def create_failure_issue(summary, description, problem_level=None, problem_service=None, 
                        naumen_failure_type=None, stream_1c=None, time_start_problem=None, 
                        influence=None, contractor_task_link=None, assignee=None):
    """
    Создание задачи типа Failure в проекте FA
    
    Args:
        summary (str): Краткое описание проблемы
        description (str): Подробное описание проблемы
        problem_level (str): Уровень проблемы
        problem_service (str): Затронутый сервис
        naumen_failure_type (str): Тип проблемы в Naumen
        stream_1c (str): Поток 1С
        time_start_problem (str): Время начала проблемы
        influence (str): Влияние на
        contractor_task_link (str): Ссылка на задачу в ТП подрядчика
        assignee (str): Исполнитель
    
    Returns:
        dict: Информация о созданной задаче или None в случае ошибки
    """
    try:
        # Настройка сессии
        session = requests.Session()
        session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CONFIG["JIRA"]["TOKEN"]}'
        })
        
        # Базовый URL для API
        base_url = urljoin(CONFIG["JIRA"]["LOGIN_URL"].strip(), '/rest/api/2/')
        
        # Подготовка данных для создания задачи
        issue_data = {
            "fields": {
                "project": {
                    "key": "FA"
                },
                "summary": summary,
                "description": description,
                "issuetype": {
                    "name": "Failure"
                }
            }
        }
        
        # Добавление опциональных полей
        if problem_level:
            issue_data["fields"]["customfield_13117"] = {"value": problem_level}
        if problem_service:
            issue_data["fields"]["customfield_13937"] = {"value": problem_service}
        if naumen_failure_type:
            issue_data["fields"]["customfield_14074"] = {"value": naumen_failure_type}
        if stream_1c:
            issue_data["fields"]["customfield_17317"] = {"value": stream_1c}
        if time_start_problem:
            # Преобразование времени в формат ISO 8601 с часовым поясом
            try:
                dt = datetime.strptime(time_start_problem, "%Y-%m-%d %H:%M")
                # Добавляем часовой пояс UTC+3 (Москва)
                issue_data["fields"]["customfield_13119"] = dt.strftime("%Y-%m-%dT%H:%M:00.000+0300")
            except ValueError:
                print("Ошибка: Неверный формат времени")
                return None
        if influence:
            issue_data["fields"]["customfield_17107"] = {"value": influence}
        
        # Вывод данных для отладки
        print("\nОтправляемые данные:")
        print(json.dumps(issue_data, ensure_ascii=False, indent=2))
        
        # Создание задачи
        print("\nСоздание задачи...")
        response = session.post(
            urljoin(base_url, 'issue'),
            json=issue_data
        )
        response.raise_for_status()
        
        created_issue = response.json()
        print(f"\nЗадача успешно создана: {created_issue['key']}")
        print(f"URL: {CONFIG['JIRA']['LOGIN_URL']}/browse/{created_issue['key']}")
        
        return created_issue
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при создании задачи: {str(e)}")
        if e.response is not None:
            if e.response.status_code == 401:
                print("\nОшибка аутентификации. Проверьте правильность API токена")
            elif e.response.status_code == 403:
                print("\nОшибка доступа. Проверьте права доступа к проекту")
            elif e.response.status_code == 400:
                print("\nОшибка в данных задачи. Проверьте правильность заполнения полей")
                try:
                    error_details = e.response.json()
                    print("\nДетали ошибки:")
                    print(json.dumps(error_details, ensure_ascii=False, indent=2))
                except:
                    print("\nТекст ответа:")
                    print(e.response.text)
        return None

def get_input_with_options(prompt, options, allow_empty=False):
    """
    Получение ввода с выбором из списка опций
    
    Args:
        prompt (str): Текст запроса
        options (list): Список доступных опций
        allow_empty (bool): Разрешить пустой ввод
    
    Returns:
        str: Выбранная опция или None
    """
    while True:
        print(f"\n{prompt}")
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        
        choice = input("\nВыберите номер (или Enter для пропуска): ").strip()
        if not choice and allow_empty:
            return None
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(options):
                return options[index]
        except ValueError:
            pass
        
        print(f"Ошибка: Выберите число от 1 до {len(options)}")

def main():
    # Проверка конфигурации
    if not check_config():
        sys.exit(1)
    
    print("\n=== Создание задачи типа Failure ===")
    
    # Получение обязательных полей
    summary = input("\nВведите краткое описание проблемы: ").strip()
    while not summary:
        print("Ошибка: Краткое описание не может быть пустым")
        summary = input("Введите краткое описание проблемы: ").strip()
    
    description = input("\nВведите подробное описание проблемы: ").strip()
    while not description:
        print("Ошибка: Подробное описание не может быть пустым")
        description = input("Введите подробное описание проблемы: ").strip()
    
    # Получение опциональных полей
    problem_levels = [
        "Замедление работы сервиса",
        "Полная недоступность сервиса",
        "Частичная недоступность сервиса",
        "Проблемы в работе сервиса",
        "Потенциальная недоступность сервиса"
    ]
    problem_level = get_input_with_options("Выберите уровень проблемы:", problem_levels, False)
    while not problem_level:
        print("Ошибка: Уровень проблемы обязателен")
        problem_level = get_input_with_options("Выберите уровень проблемы:", problem_levels, False)
    
    problem_services = [
        "Naumen", "Электронная почта", "УТЦ", "УТ Юнион", "1С УТ СПБ", "1С УТ СЗФО",
        "1С УТ МСК", "1С ЦФС", "УТ СПБ+УТ СЗФО+ УТ МСК", "LMS", "Проблема с обменами",
        "Сеть и интернет 1 подразделения", "Удалённый рабочий стол RDP (trm)",
        "Удалённый рабочий стол RDP для КЦ (retrm)", "VPN офисный", "VPN ДО КЦ",
        "Стационарная телефония", "Мобильная телефония", "Сетевое хранилище (Диск Х)",
        "Сайт Petrovich.ru", "Чат на сайте", "Jira", "Confluence", "Petlocal.ru",
        "Электроэнергия", "Телеопти/Май тайм", "Сервис оплаты", "Jira + Confluence",
        "b2b.stdp.ru", "Skype for business(Lync)", "DocsVision (DV)", "УТ СПБ",
        "ЗУП", "HR-Link", "WMS", "Мобильное приложение", "Другое"
    ]
    problem_service = get_input_with_options("Выберите затронутый сервис:", problem_services, False)
    while not problem_service:
        print("Ошибка: Затронутый сервис обязателен")
        problem_service = get_input_with_options("Выберите затронутый сервис:", problem_services, False)
    
    naumen_failure_types = [
        "Голосовой канал", "Авторизация", "Softphone", "Анкета", "Кейсы с сайта",
        "Почтовый канал", "Чат (VK, WA, Telegram, Webim)", "Отчёты", "Другое"
    ]
    naumen_failure_type = get_input_with_options("Выберите тип проблемы в Naumen:", naumen_failure_types, True)
    
    stream_1c_options = [
        "Интеграция", "Коммерция", "Маркетинг", "ОПТ", "ПиКК", "Розница (СТЦ/КЦ)",
        "Сервисы оплат", "Складская логистика", "Транспортная логистика",
        "Финансы", "ЭДО"
    ]
    stream_1c = get_input_with_options("Выберите поток 1С:", stream_1c_options, True)
    
    print("\nВыберите время начала проблемы:")
    print("1. Указать вручную")
    print("2. Использовать текущее время")
    
    time_choice = input("\nВыберите вариант (1-2) [2]: ").strip() or "2"
    
    if time_choice == "1":
        time_start_problem = input("\nВведите время начала проблемы (YYYY-MM-DD HH:mm): ").strip()
        if time_start_problem:
            try:
                datetime.strptime(time_start_problem, "%Y-%m-%d %H:%M")
            except ValueError:
                print("Ошибка: Неверный формат даты. Используйте формат YYYY-MM-DD HH:mm")
                time_start_problem = None
    else:
        time_start_problem = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f"\nУстановлено текущее время: {time_start_problem}")
    
    influence_options = ["Клиенты", "Бизнес-функция", "Сотрудники"]
    influence = get_input_with_options("Выберите влияние на:", influence_options, True)
    
    contractor_task_link = input("\nВведите ссылку на задачу в ТП подрядчика: ").strip()
    
    assignee = input("\nВведите логин исполнителя (или Enter для пропуска): ").strip()
    
    # Создание задачи
    create_failure_issue(
        summary=summary,
        description=description,
        problem_level=problem_level,
        problem_service=problem_service,
        naumen_failure_type=naumen_failure_type,
        stream_1c=stream_1c,
        time_start_problem=time_start_problem,
        influence=influence,
        contractor_task_link=contractor_task_link,
        assignee=assignee
    )

if __name__ == "__main__":
    main() 