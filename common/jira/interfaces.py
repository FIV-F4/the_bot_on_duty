from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime


class JiraIssue(ABC):
    """Интерфейс для задачи JIRA."""
    
    @property
    @abstractmethod
    def key(self) -> str:
        """Ключ задачи."""
        pass
    
    @property
    @abstractmethod
    def summary(self) -> str:
        """Краткое описание задачи."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Полное описание задачи."""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """Статус задачи."""
        pass
    
    @property
    @abstractmethod
    def assignee(self) -> Optional[str]:
        """Исполнитель задачи."""
        pass
    
    @property
    @abstractmethod
    def created(self) -> datetime:
        """Дата создания задачи."""
        pass
    
    @property
    @abstractmethod
    def updated(self) -> datetime:
        """Дата обновления задачи."""
        pass


class JiraClient(ABC):
    """Интерфейс для клиента JIRA."""
    
    @abstractmethod
    async def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str,
        **kwargs
    ) -> JiraIssue:
        """
        Создание новой задачи.
        
        Args:
            project_key: Ключ проекта
            summary: Краткое описание
            description: Полное описание
            issue_type: Тип задачи
            **kwargs: Дополнительные параметры
            
        Returns:
            Созданная задача
        """
        pass
    
    @abstractmethod
    async def get_issue(self, issue_key: str) -> JiraIssue:
        """
        Получение задачи по ключу.
        
        Args:
            issue_key: Ключ задачи
            
        Returns:
            Задача
        """
        pass
    
    @abstractmethod
    async def update_issue(
        self,
        issue_key: str,
        **kwargs
    ) -> JiraIssue:
        """
        Обновление задачи.
        
        Args:
            issue_key: Ключ задачи
            **kwargs: Поля для обновления
            
        Returns:
            Обновленная задача
        """
        pass
    
    @abstractmethod
    async def transition_issue(
        self,
        issue_key: str,
        transition_id: str
    ) -> JiraIssue:
        """
        Изменение статуса задачи.
        
        Args:
            issue_key: Ключ задачи
            transition_id: ID перехода
            
        Returns:
            Обновленная задача
        """
        pass
    
    @abstractmethod
    async def search_issues(
        self,
        jql: str,
        max_results: int = 50
    ) -> List[JiraIssue]:
        """
        Поиск задач по JQL.
        
        Args:
            jql: JQL запрос
            max_results: Максимальное количество результатов
            
        Returns:
            Список найденных задач
        """
        pass
    
    @abstractmethod
    async def add_comment(
        self,
        issue_key: str,
        comment: str
    ) -> Dict[str, Any]:
        """
        Добавление комментария к задаче.
        
        Args:
            issue_key: Ключ задачи
            comment: Текст комментария
            
        Returns:
            Информация о созданном комментарии
        """
        pass 