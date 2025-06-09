import aiohttp
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from functools import wraps
import time
import requests

from .interfaces import JiraClient, JiraIssue
from .models import JiraIssueModel, JiraTransition, JiraComment
from .exceptions import (
    JiraError, JiraConnectionError, JiraAuthenticationError,
    JiraNotFoundError, JiraValidationError, JiraPermissionError,
    JiraRateLimitError, JiraTransitionError, JiraCommentError
)
from .config import JiraConfig


def handle_jira_errors(func):
    """Декоратор для обработки ошибок JIRA."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except aiohttp.ClientError as e:
            raise JiraConnectionError(f"Ошибка подключения к JIRA: {str(e)}")
        except aiohttp.ClientResponseError as e:
            if e.status == 400:
                raise JiraValidationError(f"Ошибка валидации JIRA: {str(e)}")
            elif e.status == 401:
                raise JiraAuthenticationError("Ошибка аутентификации в JIRA")
            elif e.status == 403:
                raise JiraPermissionError("Недостаточно прав для выполнения операции")
            elif e.status == 404:
                raise JiraNotFoundError("Запрашиваемый ресурс не найден")
            elif e.status == 429:
                raise JiraRateLimitError("Превышен лимит запросов к JIRA")
            else:
                raise JiraError(f"Ошибка JIRA: {str(e)}")
    return wrapper


class JiraApiClient(JiraClient):
    """Клиент для работы с JIRA API."""
    
    def __init__(self, config: JiraConfig):
        self.config = config
        self.base_url = f"{config.JIRA_URL}/rest/api/{config.API_VERSION}"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config.JIRA_API_TOKEN}'
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
    
    async def __aenter__(self):
        """Создание сессии при входе в контекстный менеджер."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии при выходе из контекстного менеджера."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Получение данных из кэша."""
        if key in self._cache:
            if time.time() - self._cache_timestamps[key] < self.config.CACHE_TTL:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._cache_timestamps[key]
        return None
    
    def _set_cached(self, key: str, value: Any):
        """Сохранение данных в кэш."""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()
    
    @handle_jira_errors
    async def create_issue(self, issue_data: dict) -> JiraIssue:
        """
        Создает новую задачу в JIRA.
        
        Args:
            issue_data (dict): Данные для создания задачи в формате JIRA API
            
        Returns:
            JiraIssue: Созданная задача
            
        Raises:
            JiraError: При ошибке создания задачи
        """
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")

        async with self.session.post(
            f"{self.base_url}/issue",
            json=issue_data,
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
            issue_key = data.get('key')
            if not issue_key:
                raise JiraError(f"Не удалось получить ключ созданной задачи: {data}")

            # Получаем полную информацию о созданной задаче
            return await self.get_issue(issue_key)
    
    @handle_jira_errors
    async def get_issue(self, issue_key: str) -> JiraIssue:
        """
        Получает информацию о задаче по её ключу.
        
        Args:
            issue_key: Ключ задачи (например, "PROJ-123")
            
        Returns:
            JiraIssue: Объект задачи
            
        Raises:
            JiraError: При ошибке получения задачи
            JiraNotFoundError: Если задача не найдена
        """
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")

        async with self.session.get(
            f"{self.base_url}/issue/{issue_key}",
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            try:
                response.raise_for_status()  # Сначала проверяем статус
                result = await response.json()
                if "errorMessages" in result:
                    raise JiraNotFoundError(f"Задача не найдена: {result['errorMessages'][0]}")
                issue = JiraIssueModel.from_raw_data(result)
                return issue
            except aiohttp.ClientResponseError as e:
                if e.status == 404:
                    raise JiraNotFoundError(f"Задача {issue_key} не найдена")
                raise
    
    @handle_jira_errors
    async def get_all_projects(self) -> List[Dict[str, Any]]:
        """Получение всех доступных проектов."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")

        async with self.session.get(
            f"{self.base_url}/project",
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    @handle_jira_errors
    async def get_create_issue_metadata(
        self,
        project_key: Optional[str] = None,
        issue_type_id: Optional[str] = None,
        expand: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение метаданных для создания задачи, включая обязательные поля."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")
        
        params = {}
        if project_key:
            params["projectKeys"] = project_key
        if issue_type_id:
            params["issuetypeIds"] = issue_type_id
        if expand:
            params["expand"] = expand
            
        async with self.session.get(
            f"{self.base_url}/issue/createmeta",
            params=params,
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    @handle_jira_errors
    async def get_issue_types(self) -> List[Dict[str, Any]]:
        """Получение всех доступных типов задач."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")

        async with self.session.get(
            f"{self.base_url}/issuetype",
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    @handle_jira_errors
    async def update_issue(
        self,
        issue_key: str,
        **kwargs
    ) -> JiraIssue:
        """Обновление задачи."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")
        
        data = {"fields": kwargs}
        
        async with self.session.put(
            f"{self.base_url}/issue/{issue_key}",
            json=data,
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            result = await response.json()
            issue = JiraIssueModel.from_raw_data(result)
            self._set_cached(f"issue_{issue_key}", issue)
            return issue
    
    @handle_jira_errors
    async def transition_issue(
        self,
        issue_key: str,
        transition_id: str
    ) -> JiraIssue:
        """Изменение статуса задачи."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")
        
        data = {"transition": {"id": transition_id}}
        
        async with self.session.post(
            f"{self.base_url}/issue/{issue_key}/transitions",
            json=data,
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            return await self.get_issue(issue_key)
    
    @handle_jira_errors
    async def search_issues(
        self,
        jql: str,
        max_results: int = 50
    ) -> List[JiraIssue]:
        """Поиск задач по JQL."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")
        
        params = {
            "jql": jql,
            "maxResults": max_results
        }
        
        async with self.session.get(
            f"{self.base_url}/search",
            params=params,
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return [JiraIssueModel.from_raw_data(issue) for issue in result["issues"]]
    
    @handle_jira_errors
    async def add_comment(
        self,
        issue_key: str,
        comment: str
    ) -> Dict[str, Any]:
        """Добавление комментария к задаче."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")
        
        data = {"body": comment}
        
        async with self.session.post(
            f"{self.base_url}/issue/{issue_key}/comment",
            json=data,
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    @handle_jira_errors
    async def get_transitions(self, issue_key: str) -> List[JiraTransition]:
        """Получение доступных переходов для задачи."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")
        
        async with self.session.get(
            f"{self.base_url}/issue/{issue_key}/transitions",
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return [JiraTransition.from_raw_data(t) for t in result["transitions"]]
    
    @handle_jira_errors
    async def get_comments(self, issue_key: str) -> List[JiraComment]:
        """Получение комментариев задачи."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")
        
        async with self.session.get(
            f"{self.base_url}/issue/{issue_key}/comment",
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return [JiraComment.from_raw_data(c) for c in result["comments"]] 