from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class User:
    """Сущность пользователя"""
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime
    last_activity: datetime
    is_active: bool = True
    
    def __post_init__(self):
        if not isinstance(self.created_at, datetime):
            self.created_at = datetime.fromisoformat(self.created_at)
        if not isinstance(self.last_activity, datetime):
            self.last_activity = datetime.fromisoformat(self.last_activity) 