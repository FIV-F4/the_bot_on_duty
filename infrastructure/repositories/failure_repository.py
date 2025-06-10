from datetime import datetime, timedelta
from typing import List, Optional
import json
import os

from domain.entities.failure import Failure, FailureStatus
from domain.interfaces.failure_repository import FailureRepository

class FileFailureRepository(FailureRepository):
    """Реализация репозитория сбоев с хранением в файле"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Убедиться, что файл существует"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)
    
    def _load_failures(self) -> List[dict]:
        """Загрузить сбои из файла"""
        with open(self.file_path, 'r') as f:
            return json.load(f)
    
    def _save_failures(self, failures: List[dict]) -> None:
        """Сохранить сбои в файл"""
        with open(self.file_path, 'w') as f:
            json.dump(failures, f, indent=2)
    
    def _dict_to_failure(self, data: dict) -> Failure:
        """Преобразовать словарь в объект Failure"""
        return Failure(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            created_by=data['created_by'],
            created_at=datetime.fromisoformat(data['created_at']),
            status=FailureStatus(data['status']),
            telegram_thread_id=data.get('telegram_thread_id'),
            extended_by=data.get('extended_by'),
            extended_at=datetime.fromisoformat(data['extended_at']) if data.get('extended_at') else None,
            resolved_at=datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None
        )
    
    def _failure_to_dict(self, failure: Failure) -> dict:
        """Преобразовать объект Failure в словарь"""
        return {
            'id': failure.id,
            'title': failure.title,
            'description': failure.description,
            'created_by': failure.created_by,
            'created_at': failure.created_at.isoformat(),
            'status': failure.status.value,
            'telegram_thread_id': failure.telegram_thread_id,
            'extended_by': failure.extended_by,
            'extended_at': failure.extended_at.isoformat() if failure.extended_at else None,
            'resolved_at': failure.resolved_at.isoformat() if failure.resolved_at else None
        }
    
    async def create(self, failure: Failure) -> None:
        """Создать новый сбой"""
        failures = self._load_failures()
        
        # Генерируем ID
        failure.id = max([f['id'] for f in failures], default=0) + 1
        
        # Добавляем сбой
        failures.append(self._failure_to_dict(failure))
        self._save_failures(failures)
    
    async def get(self, failure_id: int) -> Optional[Failure]:
        """Получить сбой по ID"""
        failures = self._load_failures()
        for data in failures:
            if data['id'] == failure_id:
                return self._dict_to_failure(data)
        return None
    
    async def get_active(self) -> List[Failure]:
        """Получить активные сбои"""
        failures = self._load_failures()
        return [
            self._dict_to_failure(data)
            for data in failures
            if data['status'] == FailureStatus.ACTIVE.value
        ]
    
    async def update(self, failure: Failure) -> None:
        """Обновить сбой"""
        failures = self._load_failures()
        for i, data in enumerate(failures):
            if data['id'] == failure.id:
                failures[i] = self._failure_to_dict(failure)
                break
        self._save_failures(failures)
    
    async def update_status(
        self,
        failure_id: int,
        status: FailureStatus
    ) -> None:
        """Обновить статус сбоя"""
        failure = await self.get(failure_id)
        if failure:
            failure.status = status
            await self.update(failure)
    
    async def get_needs_extension(self) -> List[Failure]:
        """Получить сбои, которые нужно продлить"""
        now = datetime.now()
        failures = self._load_failures()
        return [
            self._dict_to_failure(data)
            for data in failures
            if (
                data['status'] == FailureStatus.ACTIVE.value and
                datetime.fromisoformat(data['created_at']) + timedelta(hours=24) <= now
            )
        ]
    
    async def get_needs_resolution(self) -> List[Failure]:
        """Получить сбои, которые нужно разрешить"""
        now = datetime.now()
        failures = self._load_failures()
        return [
            self._dict_to_failure(data)
            for data in failures
            if (
                data['status'] in [FailureStatus.ACTIVE.value, FailureStatus.EXTENDED.value] and
                datetime.fromisoformat(data['created_at']) + timedelta(hours=48) <= now
            )
        ] 