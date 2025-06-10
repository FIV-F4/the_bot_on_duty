# Документация по модулю JIRA

## Обзор
Модуль JIRA предоставляет интерфейс для взаимодействия с JIRA API. Он реализует основные операции с задачами, проектами и метаданными.

## Структура модуля
```
common/jira/
├── client.py          # Основной клиент для работы с JIRA API
├── models.py          # Модели данных
├── config.py          # Конфигурация клиента
├── exceptions.py      # Исключения
├── interfaces.py      # Абстрактные классы и интерфейсы
├── example.py         # Примеры использования
├── info_viewer.py     # Утилита для просмотра информации
└── tests/            # Тесты
    └── test_client.py # Тесты клиента
```

## Компоненты модуля

### Интерфейсы (interfaces.py)
Модуль определяет два основных интерфейса:

#### JiraIssue
Абстрактный класс, описывающий структуру задачи:
- `key` - ключ задачи
- `summary` - краткое описание
- `description` - полное описание
- `status` - статус задачи
- `assignee` - исполнитель
- `created` - дата создания
- `updated` - дата обновления

#### JiraClient
Абстрактный класс, определяющий основные операции с JIRA:
- `create_issue` - создание задачи
- `get_issue` - получение задачи
- `update_issue` - обновление задачи
- `transition_issue` - изменение статуса
- `search_issues` - поиск задач
- `add_comment` - добавление комментария

### Утилиты

#### info_viewer.py
Утилита для просмотра информации о проектах и метаданных:
- Просмотр доступных проектов
- Просмотр типов задач
- Просмотр обязательных полей для создания задач

#### example.py
Примеры использования клиента:
- Создание задачи
- Получение типов задач
- Работа с метаданными
- Добавление комментариев
- Изменение статуса
- Поиск задач

### Исключения (exceptions.py)
Модуль определяет следующие исключения:
- `JiraError` - базовое исключение
- `JiraConnectionError` - ошибки подключения
- `JiraAuthenticationError` - ошибки аутентификации
- `JiraNotFoundError` - ресурс не найден
- `JiraValidationError` - ошибки валидации
- `JiraPermissionError` - недостаточно прав
- `JiraRateLimitError` - превышен лимит запросов
- `JiraTransitionError` - ошибки при смене статуса
- `JiraCommentError` - ошибки при работе с комментариями

## Установка и настройка

### Зависимости
```bash
pip install aiohttp pytest pytest-asyncio python-dotenv pydantic pydantic-settings
```

### Конфигурация
```python
from common.jira.config import JiraConfig

config = JiraConfig(
    JIRA_URL="https://your-jira.com",
    JIRA_API_TOKEN="your-api-token",  # API токен для доступа к JIRA
    JIRA_DEFAULT_PROJECT="PROJ",      # Ключ проекта по умолчанию
    REQUEST_TIMEOUT=30                # опционально
)
```

### Переменные окружения
Модуль использует следующие переменные окружения (можно задать в файле `.env`):
```
JIRA_URL=https://your-jira.com
JIRA_API_TOKEN=your-api-token
JIRA_DEFAULT_PROJECT=PROJ
REQUEST_TIMEOUT=30
MAX_RETRIES=3
CACHE_TTL=300
```

## Использование

### Создание клиента
```python
from common.jira.client import JiraApiClient

client = JiraApiClient(config)
```

### Основные операции

#### Создание задачи
```python
issue_data = {
    "project": {"key": "PROJ"},
    "summary": "Test issue",
    "description": "Test description",
    "issuetype": {"id": "10001"}
}
issue = await client.create_issue(issue_data)
```

#### Получение задачи
```python
issue = await client.get_issue("PROJ-123")
```

#### Поиск задач
```python
issues = await client.search_issues("project=PROJ AND status=Open")
```

#### Добавление комментария
```python
comment = await client.add_comment("PROJ-123", "Test comment")
```

#### Изменение статуса
```python
# Получение доступных переходов
transitions = await client.get_transitions("PROJ-123")

# Выполнение перехода
issue = await client.transition_issue("PROJ-123", transition_id="31")
```

## Обработка ошибок

Модуль использует следующие исключения:
- `JiraError` - базовое исключение для всех ошибок JIRA
- `JiraConnectionError` - ошибки подключения
- `JiraNotFoundError` - задача не найдена
- `JiraValidationError` - ошибки валидации данных

Пример обработки ошибок:
```python
from common.jira.exceptions import JiraError, JiraNotFoundError

try:
    issue = await client.get_issue("NONEXISTENT-1")
except JiraNotFoundError as e:
    print(f"Задача не найдена: {e}")
except JiraError as e:
    print(f"Произошла ошибка: {e}")
```

## Тестирование

### Запуск тестов
```bash
pytest common/jira/tests/
```

### Структура тестов
Тесты находятся в директории `common/jira/tests/` и используют pytest и unittest.mock для имитации сетевых запросов.

Основные тесты:
- `test_create_issue_success` - успешное создание задачи
- `test_create_issue_error` - обработка ошибок при создании
- `test_get_issue_success` - успешное получение задачи
- `test_get_issue_not_found` - обработка случая, когда задача не найдена
- `test_add_comment_success` - успешное добавление комментария
- `test_get_transitions_success` - получение доступных переходов
- `test_search_issues_success` - поиск задач
- `