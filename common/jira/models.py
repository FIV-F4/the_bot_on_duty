from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

from .interfaces import JiraIssue


@dataclass
class JiraIssueModel(JiraIssue):
    """Модель задачи JIRA."""
    
    _key: str
    _summary: str
    _description: str
    _status: str
    _assignee: Optional[str]
    _created: datetime
    _updated: datetime
    _raw_data: Dict[str, Any]
    
    @property
    def key(self) -> str:
        return self._key
    
    @property
    def summary(self) -> str:
        return self._summary
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def status(self) -> str:
        return self._status
    
    @property
    def assignee(self) -> Optional[str]:
        return self._assignee
    
    @property
    def created(self) -> datetime:
        return self._created
    
    @property
    def updated(self) -> datetime:
        return self._updated
    
    @classmethod
    def from_raw_data(cls, data: Dict[str, Any]) -> "JiraIssueModel":
        """
        Создание модели из сырых данных JIRA.
        
        Args:
            data: Сырые данные от JIRA API
            
        Returns:
            Модель задачи
        """
        fields = data["fields"]
        return cls(
            _key=data["key"],
            _summary=fields["summary"],
            _description=fields.get("description", ""),
            _status=fields["status"]["name"],
            _assignee=fields.get("assignee", {}).get("displayName"),
            _created=datetime.fromisoformat(fields["created"].replace("Z", "+00:00")),
            _updated=datetime.fromisoformat(fields["updated"].replace("Z", "+00:00")),
            _raw_data=data
        )


@dataclass
class JiraTransition:
    """Модель перехода статуса в JIRA."""
    
    id: str
    name: str
    to_status: str
    has_screen: bool
    is_global: bool
    is_initial: bool
    is_conditional: bool
    
    @classmethod
    def from_raw_data(cls, data: Dict[str, Any]) -> "JiraTransition":
        """
        Создание модели из сырых данных JIRA.
        
        Args:
            data: Сырые данные от JIRA API
            
        Returns:
            Модель перехода
        """
        return cls(
            id=data["id"],
            name=data["name"],
            to_status=data["to"]["name"],
            has_screen=data.get("hasScreen", False),
            is_global=data.get("isGlobal", False),
            is_initial=data.get("isInitial", False),
            is_conditional=data.get("isConditional", False)
        )


@dataclass
class JiraComment:
    """Модель комментария в JIRA."""
    
    id: str
    body: str
    author: str
    created: datetime
    updated: datetime
    
    @classmethod
    def from_raw_data(cls, data: Dict[str, Any]) -> "JiraComment":
        """
        Создание модели из сырых данных JIRA.
        
        Args:
            data: Сырые данные от JIRA API
            
        Returns:
            Модель комментария
        """
        return cls(
            id=data["id"],
            body=data["body"],
            author=data["author"]["displayName"],
            created=datetime.fromisoformat(data["created"].replace("Z", "+00:00")),
            updated=datetime.fromisoformat(data["updated"].replace("Z", "+00:00"))
        ) 