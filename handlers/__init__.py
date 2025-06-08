# handlers/__init__.py

# Импорт роутеров из модулей
from .start_help import router as start_help_router
from .alarm_handlers import router as alarm_router
from .screenshot import router as screenshot_router
from .manage_handlers import router as stop_router
from .current_events import router as current_events_router

# Список всех роутеров для регистрации в диспетчере
routers = [
    start_help_router,
    alarm_router,
    screenshot_router,
    stop_router,
    current_events_router
]

# Экспорт для удобства
__all__ = ["routers"]