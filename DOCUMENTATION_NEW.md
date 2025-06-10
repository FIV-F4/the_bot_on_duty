# Документация по боту

## Структура проекта

```
the_bot_on_duty/
├── application/                    # Слой приложения
│   ├── handlers/                  # Обработчики команд
│   ├── services/                  # Сервисы приложения
│   ├── interfaces/                # Интерфейсы
│   └── use_cases/                 # Сценарии использования
│
├── infrastructure/                # Инфраструктурный слой
│   ├── telegram/                  # Интеграция с Telegram
│   ├── repositories/              # Репозитории данных
│   ├── selenium/                  # Интеграция с Selenium
│   ├── confluence/               # Интеграция с Confluence
│   ├── jira/                     # Интеграция с JIRA
│   ├── database/                 # Работа с базой данных
│   └── external/                 # Внешние интеграции
│
├── domain/                       # Доменный слой
│   ├── entities/                 # Бизнес-сущности
│   ├── value_objects/           # Объекты-значения
│   └── services/                # Доменные сервисы
│
├── core/                         # Ядро приложения
│   ├── config/                  # Конфигурация
│   └── logging/                 # Логирование
│
├── utils/                        # Вспомогательные утилиты
├── tests/                        # Тесты
├── docs/                         # Документация
├── scripts/                      # Скрипты
│
├── fa_bot.py                     # Основной класс бота
├── fa_bot copy.py                # Резервная копия бота
├── main.py                       # Точка входа
├── config.py                     # Конфигурация
├── config.json                   # JSON конфигурация
├── keyboards.py                  # Клавиатуры Telegram
├── bot_state.py                  # Состояние бота
├── reset_state.py                # Сброс состояния
├── selenium_utils.py             # Утилиты для Selenium
├── utils.py                      # Общие утилиты
├── logger.py                     # Настройка логирования
├── bot.log                       # Лог бота
├── fa_bot.log                    # Лог основного бота
├── requirements.txt              # Зависимости
├── requirements-dev.txt          # Зависимости для разработки
├── build.sh                      # Скрипт сборки
├── LICENSE                       # Лицензия
└── README.md                     # Документация проекта
```
## Структура к которой идём
the_bot_on_duty/
├── bots/
│   ├── duty_bot/
│   │   ├── application/
│   │   │   ├── handlers/
│   │   │   ├── services/
│   │   │   ├── interfaces/
│   │   │   └── use_cases/
│   │   ├── infrastructure/
│   │   │   ├── telegram/
│   │   │   ├── repositories/
│   │   │   ├── selenium/
│   │   │   ├── confluence/
│   │   │   ├── jira/
│   │   │   ├── database/
│   │   │   └── external/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   ├── value_objects/
│   │   │   └── services/
│   │   ├── core/
│   │   │   ├── config/
│   │   │   └── logging/
│   │   ├── tests/
│   │   ├── .env
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── keyboards.py
│   │   ├── bot_state.py
│   │   ├── reset_state.py
│   │   ├── fa_bot.py
│   │   ├── fa_bot copy.py
│   │   └── README.md
│   ├── notifier_bot/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── domain/
│   │   ├── core/
│   │   ├── tests/
│   │   ├── .env
│   │   ├── config.py
│   │   ├── main.py
│   │   └── README.md
│   ├── jira_creator_bot/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── domain/
│   │   ├── core/
│   │   ├── tests/
│   │   ├── .env
│   │   ├── config.py
│   │   ├── main.py
│   │   └── README.md
│   ├── contact_center_bot/
│   │   ├── config.py
│   │   ├── handlers.py
│   │   ├── keyboards.py
│   │   ├── main.py
│   │   └── states.py
│   ├── ... (другие боты)
│
├── common/
│   ├── telegram/
│   │   ├── launcher.py
│   │   ├── middlewares.py
│   │   ├── filters.py
│   │   ├── router.py
│   │   └── callbacks.py
│   ├── auth/
│   │   ├── policy.py
│   │   ├── user_roles.py
│   │   └── session.py
│   ├── db/
│   │   ├── models.py
│   │   ├── base.py
│   │   └── session.py
│   ├── selenium/
│   │   └── utils.py
│   ├── logging/
│   │   └── logger.py
│   ├── utils/
│   │   ├── time.py
│   │   ├── files.py
│   │   ├── retry.py
│   │   └── encoding.py
│   ├── config/
│   │   ├── env_loader.py
│   │   ├── base_config.py
│   │   └── telegram_config.py
│   ├── domain/
│   │   ├── user.py
│   │   ├── report.py
│   │   └── exceptions.py
│   └── README.md
│
├── scripts/
│   ├── build.sh
│   └── deploy.sh
├── docs/
│   └── architecture.md
├── tests/
│   ├── common/
│   └── integration/
├── .env                          # Общие переменные (DEBUG, LOG_LEVEL, общие урлы)
├── .env.example                  # Шаблон для новых .env
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── poetry.lock
├── LICENSE
└── README.md


### Примечания по структуре:
- `fa_bot.py` - основной класс бота, содержащий всю логику работы
- `fa_bot copy.py` - резервная копия основного файла бота
- `bot_state.py` и `reset_state.py` - управление состоянием бота
- `selenium_utils.py` - утилиты для работы с Selenium
- `config.py` и `config.json` - конфигурационные файлы
- `keyboards.py` - определение клавиатур для Telegram

## Зависимости
### Основные библиотеки
- aiogram - фреймворк для работы с Telegram Bot API
- asyncio - для асинхронного выполнения операций
- selenium - для создания скриншотов
- logging - для логирования
- json - для работы с данными состояния

### Конфигурация
- Токен Telegram бота
- ID канала для уведомлений
- Учетные данные JIRA/Confluence
- Список администраторов
- Таймауты и настройки

### Безопасность
- Проверка прав доступа
- Безопасное хранение токенов
- Валидация входящих данных
- Защита от дублирования запуска

### Логирование
- Двухуровневое логирование (файл + консоль)
- Формат: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`
- Уровни: INFO, WARNING, ERROR, CRITICAL

## Общее описание
Бот представляет собой Telegram-приложение, написанное с использованием библиотеки aiogram. Он предназначен для управления событиями, авариями и регламентными работами.

## Основные компоненты

### 1. Точка входа (main.py)
Основной файл, который инициализирует и запускает бота. Содержит следующие ключевые компоненты:

#### Инициализация и настройка
- Настройка логирования (файл и консоль)
- Проверка наличия токена Telegram
- Инициализация бота и диспетчера
- Загрузка состояния бота

#### Регистрация обработчиков
Бот использует следующие роутеры:
- `start_help` - обработка команд start и help
- `alarm_handlers` - обработка аварийных ситуаций
- `screenshot` - работа со скриншотами
- `manage_handlers` - управление событиями
- `current_events_router` - обработка текущих событий

#### Команды бота
- `/start` - запуск бота
- `/help` - помощь
- `/view` - просмотр JIRA/Confluence
- `/new_message` - создание сообщения
- `/manage` - управление событиями
- `/alarm_list` - список активных событий

### 2. Управление состоянием (bot_state.py)
Класс `BotState` отвечает за управление состоянием бота. Основные функции:

#### Хранение данных
- Активные аварии (`active_alarms`)
- Состояния пользователей (`user_states`)
- Регламентные работы (`active_maintenances`)
- Очередь расширений (`extension_queue`)

#### Основные методы
- `save_state()` - сохранение состояния в файл
- `load_state()` - загрузка состояния из файла
- `get_user_active_alarms()` - получение активных аварий пользователя
- `get_user_active_maintenances()` - получение активных регламентных работ

### 3. Обработчики команд

#### Стартовые команды (start_help.py)
- Команда `/start` - приветствие и основное меню
- Команда `/help` - справка по командам
- Глобальная отмена - очистка состояния

#### Обработчики аварий (alarm_handlers.py)

##### 1. Создание новых сообщений
- `create_new_message()` - основная функция создания сообщения
- `create_alarm_message()` - создание сообщения о сбое
- `create_work_message()` - создание сообщения о работах
- `create_regular_message()` - создание обычного сообщения

##### 2. Типы сообщений
###### Сбой (Alarm)
- Уровни сбоя (1-3)
- Выбор сервиса
- Ввод недоступных сервисов
- Подтверждение отправки
- Интеграция с JIRA

###### Работа (Work)
- Выбор типа работы
- Указание времени начала/окончания
- Выбор затронутых сервисов
- Подтверждение отправки

###### Обычное (Regular)
- Ввод текста сообщения
- Выбор получателей
- Подтверждение отправки

##### 3. Пошаговый процесс создания
1. Выбор типа сообщения
2. Заполнение обязательных полей
3. Предварительный просмотр
4. Подтверждение отправки
5. Отправка в Telegram
6. Создание задачи в JIRA (для сбоев)

##### 4. Интеграция с JIRA
- Автоматическое создание задач
- Синхронизация статусов
- Обновление информации
- Закрытие задач

##### 5. Управление состоянием
- `process_level()` - обработка уровня проблемы
- `process_service()` - обработка выбора сервиса
- `enter_unavailable_services()` - ввод недоступных сервисов
- `confirm_send_callback()` - подтверждение отправки
- `cancel_send_callback()` - отмена отправки

##### 6. Обработка ошибок
- Валидация входных данных
- Обработка исключений
- Логирование ошибок
- Уведомление администраторов

#### Обработчики управления (manage_handlers.py)
- Управление событиями
- Продление времени
- Система напоминаний
- Завершение событий

#### Обработчики скриншотов (screenshot.py)
- Создание скриншотов JIRA/Confluence
- Работа с Selenium
- Асинхронное выполнение
- Обработка ошибок

#### Обработчики текущих событий (current_events.py)
- Просмотр активных событий
- Обновление списка
- Форматированный вывод
- Управление отображением

## Модуль JIRA

### Описание
Модуль JIRA предоставляет интерфейс для взаимодействия с JIRA API. Он реализует основные операции с задачами, проектами и метаданными.

### Структура модуля
```
common/jira/
├── client.py          # Основной клиент для работы с JIRA API
├── models.py          # Модели данных
├── config.py          # Конфигурация клиента
├── exceptions.py      # Исключения
└── tests/            # Тесты
    └── test_client.py # Тесты клиента
```

### Конфигурация
Модуль использует следующие параметры конфигурации:
- `JIRA_URL` - URL вашего инстанса JIRA
- `JIRA_API_TOKEN` - API токен для доступа к JIRA (используется как Bearer token)
- `JIRA_DEFAULT_PROJECT` - Ключ проекта по умолчанию
- `REQUEST_TIMEOUT` - Таймаут запросов в секундах (по умолчанию 30)
- `MAX_RETRIES` - Максимальное количество попыток при ошибке (по умолчанию 3)
- `CACHE_TTL` - Время жизни кэша в секундах (по умолчанию 300)

### Основные классы и интерфейсы

#### JiraApiClient
Основной класс для работы с JIRA API. Реализует следующие методы:

- `create_issue(issue_data: dict) -> JiraIssue` - создание новой задачи
- `get_issue(issue_key: str) -> JiraIssue` - получение информации о задаче
- `get_all_projects() -> List[Dict[str, Any]]` - получение списка проектов
- `get_create_issue_metadata(...) -> Dict[str, Any]` - получение метаданных для создания задачи
- `get_issue_types() -> List[Dict[str, Any]]` - получение типов задач
- `update_issue(issue_key: str, **kwargs) -> JiraIssue` - обновление задачи
- `transition_issue(issue_key: str, transition_id: str) -> JiraIssue` - изменение статуса задачи
- `search_issues(jql: str, max_results: int = 50) -> List[JiraIssue]` - поиск задач
- `add_comment(issue_key: str, comment: str) -> Dict[str, Any]` - добавление комментария
- `get_transitions(issue_key: str) -> List[JiraTransition]` - получение доступных переходов
- `get_comments(issue_key: str) -> List[JiraComment]` - получение комментариев

#### Модели данных
- `JiraIssueModel` - модель задачи
- `JiraTransition` - модель перехода статуса
- `JiraComment` - модель комментария

### Обработка ошибок
Модуль использует следующие исключения:
- `JiraError` - базовое исключение для всех ошибок JIRA
- `JiraConnectionError` - ошибки подключения
- `JiraNotFoundError` - задача не найдена
- `JiraValidationError` - ошибки валидации данных

### Тестирование
Тесты модуля находятся в директории `common/jira/tests/` и используют pytest и unittest.mock для имитации сетевых запросов.

#### Основные тесты:
- `test_create_issue_success` - успешное создание задачи
- `test_create_issue_error` - обработка ошибок при создании
- `test_get_issue_success` - успешное получение задачи
- `test_get_issue_not_found` - обработка случая, когда задача не найдена
- `test_add_comment_success` - успешное добавление комментария
- `test_get_transitions_success` - получение доступных переходов
- `test_search_issues_success` - поиск задач
- `test_get_issue_types_success` - получение типов задач
- `test_get_all_projects_success` - получение списка проектов
- `test_get_create_issue_metadata_success` - получение метаданных

### Примеры использования

```python
# Создание клиента
config = JiraConfig(
    base_url="https://your-jira.com",
    username="user",
    password="pass"
)
client = JiraApiClient(config)

# Создание задачи
issue_data = {
    "project": {"key": "PROJ"},
    "summary": "Test issue",
    "description": "Test description",
    "issuetype": {"id": "10001"}
}
issue = await client.create_issue(issue_data)

# Получение задачи
issue = await client.get_issue("PROJ-123")

# Поиск задач
issues = await client.search_issues("project=PROJ AND status=Open")
```

### Зависимости
- aiohttp - для асинхронных HTTP-запросов
- pytest - для тестирования
- pytest-asyncio - для асинхронных тестов

## Процесс работы
1. При запуске бот проверяет наличие токена и файла состояния
2. Инициализирует все необходимые компоненты
3. Регистрирует обработчики команд
4. Запускает фоновую задачу проверки напоминаний
5. Начинает прослушивание сообщений
6. При остановке сохраняет текущее состояние

## Особенности реализации
- Асинхронное выполнение операций
- Потокобезопасное управление состоянием
- Сохранение состояния в JSON-формате
- Обработка ошибок и исключений
- Восстановление состояния после перезапуска
- Интеграция с внешними сервисами (JIRA, Confluence)
- Система прав доступа
- Логирование всех действий 

## Бот контакт-центра (contact_center_bot)

### Описание
Бот для создания заявок в контакт-центре. Позволяет создавать заявки о технических неполадках и больничных через Telegram.

### Структура
```
bots/contact_center_bot/
├── main.py           # Точка входа
├── handlers.py       # Обработчики команд
├── keyboards.py      # Клавиатуры
├── states.py         # Состояния FSM
└── config.py         # Конфигурация
```

### Основные функции
1. Создание заявки о технической неполадке
   - Ввод ФИО сотрудника
   - Ввод ФИО руководителя
   - Ввод описания проблемы

2. Создание заявки о больничном
   - Ввод ФИО сотрудника
   - Ввод ФИО руководителя
   - Ввод описания больничного

### Интеграция с JIRA
Заявки создаются в проекте SCHED через JIRA API. Для каждой заявки указываются:
- Тип задачи (Service Request)
- Исполнитель (firstline.ws@petrovich.ru)
- Метка "чатбот"
- Описание с данными сотрудника и руководителя

### Команды бота
- `/start` - запуск бота
- `/help` - помощь

### Клавиатуры
- Главное меню с кнопками:
  - "Тех. неполадка"
  - "Больничный"

### Состояния (FSM)
1. Техническая неполадка:
   - ENTER_EMPLOYEE_NAME
   - ENTER_MANAGER_NAME
   - ENTER_DESCRIPTION

2. Больничный:
   - ENTER_EMPLOYEE_NAME
   - ENTER_MANAGER_NAME
   - ENTER_DESCRIPTION

### Зависимости
- aiogram 3.x
- python-dotenv
- common/jira (внутренний модуль)

### Конфигурация
Необходимые переменные окружения:
- CONTACT_CENTER_BOT_TOKEN - токен Telegram бота
- JIRA_URL - URL JIRA
- JIRA_API_TOKEN - токен JIRA API

### Тестирование
Для ручного тестирования создания заявок используется скрипт:
```bash
python -m common.jira.tests.test_ticket_creator
```

### Безопасность
- Проверка прав доступа через декоратор @admin_required
- Безопасное хранение токенов в .env файле
- Валидация входящих данных

### Логирование
- Используется общий модуль логирования
- Логи сохраняются в файл и выводятся в консоль
- Уровни: INFO, WARNING, ERROR, CRITICAL

### Планы по улучшению
1. Добавить валидацию вводимых данных
2. Реализовать систему шаблонов заявок
3. Добавить возможность редактирования заявок
4. Реализовать систему уведомлений о статусе заявки 