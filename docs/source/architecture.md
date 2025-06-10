# Архитектура проекта

## Обзор
Проект построен на принципах Clean Architecture, что обеспечивает:
- Изоляцию бизнес-логики
- Независимость от внешних сервисов
- Гибкость в реализации
- Простоту тестирования

## Структура проекта
```
project/
├── bots/                    # UI-интерфейсы (Telegram)
│   ├── duty_bot/           # Бот дежурного
│   │   ├── __init__.py
│   │   ├── handlers/       # Обработчики команд
│   │   │   ├── __init__.py
│   │   │   ├── alarm.py
│   │   │   └── events.py
│   │   └── keyboards/      # Клавиатуры
│   ├── notifier_bot/       # Бот уведомлений
│   ├── jira_creator_bot/   # Бот создания задач
│   └── screenshot_bot/     # Бот скриншотов
├── application/            # Сценарии использования
│   ├── __init__.py
│   ├── use_cases/         # Конкретные сценарии
│   │   ├── __init__.py
│   │   ├── create_ticket.py
│   │   ├── send_notification.py
│   │   └── take_screenshot.py
│   └── interfaces/        # Интерфейсы для use-cases
│       ├── __init__.py
│       └── ticket_creator.py
├── domain/                # Бизнес-сущности и правила
│   ├── __init__.py
│   ├── entities/         # Бизнес-сущности
│   │   ├── __init__.py
│   │   ├── ticket.py
│   │   └── notification.py
│   ├── value_objects/    # Объекты-значения
│   │   ├── __init__.py
│   │   └── priority.py
│   └── interfaces/       # Интерфейсы репозиториев
│       ├── __init__.py
│       └── ticket_repository.py
├── infrastructure/        # Реализация внешних зависимостей
│   ├── __init__.py
│   ├── jira/
│   │   ├── __init__.py
│   │   └── jira_client.py
│   ├── confluence/
│   │   ├── __init__.py
│   │   └── confluence_client.py
│   └── selenium/
│       ├── __init__.py
│       └── screenshot_service.py
├── core/                 # Базовая инициализация
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
├── tests/               # Тесты
│   ├── __init__.py
│   ├── unit/
│   └── integration/
└── main.py             # Точка входа
```

## Слои архитектуры

### 1. Domain Layer
- Содержит бизнес-сущности и правила
- Не зависит от других слоев
- Определяет интерфейсы для внешних сервисов

### 2. Application Layer
- Реализует сценарии использования
- Координирует работу между сущностями
- Использует интерфейсы из domain layer

### 3. Infrastructure Layer
- Реализует внешние зависимости
- Содержит код для работы с Jira, Confluence и т.д.
- Реализует интерфейсы из domain layer

### 4. Presentation Layer (Bots)
- Обрабатывает взаимодействие с пользователем
- Использует use-cases из application layer
- Не содержит бизнес-логики

## Принципы

1. **Dependency Rule**
   - Внутренние слои не зависят от внешних
   - Зависимости направлены внутрь

2. **Interface Segregation**
   - Интерфейсы определены в domain layer
   - Реализации в infrastructure layer

3. **Single Responsibility**
   - Каждый модуль отвечает за одну задачу
   - Четкое разделение ответственности

4. **Open/Closed Principle**
   - Легко расширять функциональность
   - Не требует изменения существующего кода

## Примеры использования

### Создание тикета
```python
# domain/entities/ticket.py
class Ticket:
    def __init__(self, summary: str, description: str, priority: Priority):
        self.summary = summary
        self.description = description
        self.priority = priority

# domain/interfaces/ticket_repository.py
class TicketRepository(ABC):
    @abstractmethod
    async def create(self, ticket: Ticket) -> str:
        pass

# infrastructure/jira/jira_client.py
class JiraTicketRepository(TicketRepository):
    async def create(self, ticket: Ticket) -> str:
        # Реализация создания тикета в Jira
        pass

# application/use_cases/create_ticket.py
class CreateTicketUseCase:
    def __init__(self, ticket_repository: TicketRepository):
        self.ticket_repository = ticket_repository

    async def execute(self, summary: str, description: str, priority: Priority) -> str:
        ticket = Ticket(summary, description, priority)
        return await self.ticket_repository.create(ticket)
```

## Рекомендации по разработке

1. **Тестирование**
   - Unit-тесты для domain и application слоев
   - Integration-тесты для infrastructure слоя
   - E2E тесты для ботов

2. **Документация**
   - Документировать все публичные интерфейсы
   - Поддерживать актуальность архитектурной документации
   - Использовать типизацию для лучшей документации

3. **Код-ревью**
   - Проверять соответствие архитектуре
   - Следить за зависимостями между слоями
   - Оценивать тестируемость кода 