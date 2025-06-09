from typing import Optional, List
import sqlite3
from datetime import datetime

from domain.entities.user import User
from domain.interfaces.repository import Repository

class SQLiteUserRepository(Repository[User]):
    """SQLite реализация репозитория пользователей"""
    
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1
                )
            """)
    
    async def get(self, id: int) -> Optional[User]:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (id,)
            )
            row = cursor.fetchone()
            if row:
                return User(
                    user_id=row[0],
                    username=row[1],
                    first_name=row[2],
                    last_name=row[3],
                    created_at=row[4],
                    last_activity=row[5],
                    is_active=bool(row[6])
                )
            return None
    
    async def get_all(self) -> List[User]:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("SELECT * FROM users")
            return [
                User(
                    user_id=row[0],
                    username=row[1],
                    first_name=row[2],
                    last_name=row[3],
                    created_at=row[4],
                    last_activity=row[5],
                    is_active=bool(row[6])
                )
                for row in cursor.fetchall()
            ]
    
    async def add(self, entity: User) -> User:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, last_name, created_at, last_activity, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity.user_id,
                    entity.username,
                    entity.first_name,
                    entity.last_name,
                    entity.created_at.isoformat(),
                    entity.last_activity.isoformat(),
                    entity.is_active
                )
            )
            return entity
    
    async def update(self, entity: User) -> User:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                UPDATE users
                SET username = ?, first_name = ?, last_name = ?, last_activity = ?, is_active = ?
                WHERE user_id = ?
                """,
                (
                    entity.username,
                    entity.first_name,
                    entity.last_name,
                    entity.last_activity.isoformat(),
                    entity.is_active,
                    entity.user_id
                )
            )
            return entity
    
    async def delete(self, id: int) -> bool:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("DELETE FROM users WHERE user_id = ?", (id,))
            return cursor.rowcount > 0 