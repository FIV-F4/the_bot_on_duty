from typing import Optional, List
from datetime import datetime

from domain.entities.user import User
from domain.interfaces.repository import Repository

class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, user_repository: Repository[User]):
        self._repository = user_repository
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return await self._repository.get(user_id)
    
    async def get_all_users(self) -> List[User]:
        """Получить всех пользователей"""
        return await self._repository.get_all()
    
    async def create_user(self, user_id: int, username: Optional[str] = None,
                         first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """Создать нового пользователя"""
        now = datetime.now()
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            created_at=now,
            last_activity=now
        )
        return await self._repository.add(user)
    
    async def update_user_activity(self, user_id: int) -> Optional[User]:
        """Обновить время последней активности пользователя"""
        user = await self.get_user(user_id)
        if user:
            user.last_activity = datetime.now()
            return await self._repository.update(user)
        return None 