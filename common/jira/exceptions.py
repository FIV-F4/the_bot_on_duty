class JiraError(Exception):
    """Базовое исключение для ошибок JIRA."""
    pass


class JiraConnectionError(JiraError):
    """Ошибка подключения к JIRA."""
    pass


class JiraAuthenticationError(JiraError):
    """Ошибка аутентификации в JIRA."""
    pass


class JiraNotFoundError(JiraError):
    """Запрашиваемый ресурс не найден в JIRA."""
    pass


class JiraValidationError(JiraError):
    """Ошибка валидации данных для JIRA."""
    pass


class JiraPermissionError(JiraError):
    """Ошибка прав доступа в JIRA."""
    pass


class JiraRateLimitError(JiraError):
    """Превышен лимит запросов к JIRA."""
    pass


class JiraTransitionError(JiraError):
    """Ошибка при изменении статуса задачи."""
    pass


class JiraCommentError(JiraError):
    """Ошибка при работе с комментариями."""
    pass 