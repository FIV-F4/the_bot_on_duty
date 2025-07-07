"""
Анализатор JIRA заявок и Service Desk порталов.
Получает на вход две ссылки и анализирует поля проекта.
САМОДОСТАТОЧНЫЙ ФАЙЛ - работает без внешних зависимостей из проекта.
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import os
import sys
from pathlib import Path
from dataclasses import dataclass

# ============================================================================
# ЛОКАЛЬНАЯ КОНФИГУРАЦИЯ (без зависимостей от проекта)
# ============================================================================

@dataclass
class LocalJiraConfig:
    """Простая локальная конфигурация для анализатора."""
    JIRA_URL: str = "https://jira.petrovich.tech"
    JIRA_API_TOKEN: str = ""
    API_VERSION: str = "2"
    REQUEST_TIMEOUT: int = 30
    CACHE_TTL: int = 300
    
    def __post_init__(self):
        """Загружаем переменные из окружения после инициализации."""
        self.JIRA_URL = os.getenv("JIRA_URL", self.JIRA_URL)
        self.JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", self.JIRA_API_TOKEN)
    
    def is_configured(self) -> bool:
        """Проверяет, настроена ли конфигурация полностью."""
        return bool(self.JIRA_URL and self.JIRA_API_TOKEN.strip())
    
    def get_status_message(self) -> str:
        """Возвращает сообщение о статусе конфигурации."""
        if not self.JIRA_URL:
            return "❌ Не настроен JIRA_URL"
        if not self.JIRA_API_TOKEN.strip():
            return "❌ Не настроен JIRA_API_TOKEN (анализ будет ограничен)"
        return "✅ Конфигурация настроена полностью"

# ============================================================================
# ЛОКАЛЬНЫЕ ИСКЛЮЧЕНИЯ
# ============================================================================

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

# ============================================================================
# ЛОКАЛЬНЫЕ МОДЕЛИ
# ============================================================================

@dataclass
class LocalJiraIssue:
    """Простая модель задачи JIRA."""
    key: str
    summary: str
    description: str
    status: str
    assignee: Optional[str]
    created: datetime
    updated: datetime
    raw_data: Dict[str, Any]
    
    @classmethod
    def from_raw_data(cls, data: Dict[str, Any]) -> "LocalJiraIssue":
        """Создание модели из сырых данных JIRA."""
        fields = data["fields"]
        return cls(
            key=data["key"],
            summary=fields["summary"],
            description=fields.get("description", ""),
            status=fields["status"]["name"],
            assignee=fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
            created=datetime.fromisoformat(fields["created"].replace("Z", "+00:00")),
            updated=datetime.fromisoformat(fields["updated"].replace("Z", "+00:00")),
            raw_data=data
        )

# ============================================================================
# ЛОКАЛЬНЫЙ JIRA КЛИЕНТ
# ============================================================================

class LocalJiraClient:
    """Простой клиент для работы с JIRA API."""
    
    def __init__(self, config: LocalJiraConfig):
        self.config = config
        self.base_url = f"{config.JIRA_URL}/rest/api/{config.API_VERSION}"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Добавляем авторизацию если есть токен
        if config.JIRA_API_TOKEN.strip():
            self.headers['Authorization'] = f'Bearer {config.JIRA_API_TOKEN}'
        
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Создание сессии при входе в контекстный менеджер."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии при выходе из контекстного менеджера."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_issue(self, issue_key: str) -> LocalJiraIssue:
        """Получает информацию о задаче по её ключу."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")

        async with self.session.get(
            f"{self.base_url}/issue/{issue_key}",
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            if response.status == 404:
                raise JiraNotFoundError(f"Задача {issue_key} не найдена")
            elif response.status == 401:
                raise JiraAuthenticationError("Ошибка аутентификации в JIRA")
            elif response.status != 200:
                text = await response.text()
                raise JiraConnectionError(f"HTTP {response.status}: {text}")
            
            result = await response.json()
            return LocalJiraIssue.from_raw_data(result)
    
    async def get_all_projects(self) -> List[Dict[str, Any]]:
        """Получение всех доступных проектов."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")

        async with self.session.get(
            f"{self.base_url}/project",
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise JiraConnectionError(f"HTTP {response.status}: {text}")
            return await response.json()
    
    async def get_issue_types(self) -> List[Dict[str, Any]]:
        """Получение всех доступных типов задач."""
        if not self.session:
            raise JiraConnectionError("Сессия не инициализирована")

        async with self.session.get(
            f"{self.base_url}/issuetype",
            timeout=self.config.REQUEST_TIMEOUT
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise JiraConnectionError(f"HTTP {response.status}: {text}")
            return await response.json()
    
    async def get_create_issue_metadata(
        self,
        project_key: Optional[str] = None,
        issue_type_id: Optional[str] = None,
        expand: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение метаданных для создания задачи."""
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
            if response.status != 200:
                text = await response.text()
                raise JiraConnectionError(f"HTTP {response.status}: {text}")
            return await response.json()

# ============================================================================
# ОСНОВНОЙ АНАЛИЗАТОР
# ============================================================================

class JiraAnalyzer:
    """Класс для анализа JIRA заявок и Service Desk порталов."""
    
    def __init__(self, config: LocalJiraConfig):
        self.config = config
        self.client = LocalJiraClient(config)
        
    async def analyze_urls(self, jira_issue_url: str, service_desk_url: str) -> Dict[str, Any]:
        """Анализирует две ссылки и возвращает полную информацию о проекте."""
        # Очищаем URL от символа @
        jira_issue_url = jira_issue_url.lstrip('@')
        service_desk_url = service_desk_url.lstrip('@')
        
        # Извлекаем информацию из URL
        project_key, issue_key = self._parse_jira_issue_url(jira_issue_url)
        portal_id, request_type_id = self._parse_service_desk_url(service_desk_url)
        
        print(f"🔍 Анализ проекта: {project_key}")
        print(f"📋 Заявка: {issue_key}")
        print(f"🌐 Портал: {portal_id}, Тип запроса: {request_type_id}")
        
        async with self.client:
            # 1. Получаем информацию о проекте из JIRA API
            project_info = await self._get_project_info(project_key)
            
            # 2. Получаем поля проекта из API
            project_fields = await self._get_project_fields(project_key)
            
            # 3. Получаем информацию о конкретной заявке
            issue_info = await self._get_issue_info(issue_key)
            
            # 4. Получаем информацию о полях Service Desk портала
            portal_fields = await self._get_portal_fields(service_desk_url)
            
            # 5. Генерируем отчет
            report = self._generate_report(
                project_key, project_info, project_fields, 
                issue_info, portal_fields, jira_issue_url, service_desk_url
            )
            
            return report
    
    def _parse_jira_issue_url(self, url: str) -> Tuple[str, str]:
        """Парсит URL заявки JIRA и извлекает проект и ключ заявки."""
        match = re.search(r'/browse/([A-Z]+)-(\d+)', url)
        if not match:
            raise ValueError(f"Не удалось извлечь ключ заявки из URL: {url}")
        
        project_key = match.group(1)
        issue_number = match.group(2)
        issue_key = f"{project_key}-{issue_number}"
        
        return project_key, issue_key
    
    def _parse_service_desk_url(self, url: str) -> Tuple[str, str]:
        """Парсит URL Service Desk и извлекает ID портала и типа запроса."""
        match = re.search(r'/portal/(\d+)/create/(\d+)', url)
        if not match:
            raise ValueError(f"Не удалось извлечь ID портала и типа запроса из URL: {url}")
        
        portal_id = match.group(1)
        request_type_id = match.group(2)
        
        return portal_id, request_type_id
    
    async def _get_project_info(self, project_key: str) -> Dict[str, Any]:
        """Получает основную информацию о проекте."""
        try:
            projects = await self.client.get_all_projects()
            for project in projects:
                if project['key'] == project_key:
                    return project
            return {"key": project_key, "name": f"Проект {project_key}", "error": f"Проект {project_key} не найден"}
        except Exception as e:
            print(f"⚠️ Ошибка при получении информации о проекте: {e}")
            return {"key": project_key, "name": f"Проект {project_key}", "error": str(e)}
    
    async def _get_project_fields(self, project_key: str) -> Dict[str, Any]:
        """Получает поля проекта из JIRA API."""
        try:
            issue_types = await self.client.get_issue_types()
            metadata = await self.client.get_create_issue_metadata(
                project_key=project_key,
                expand="projects.issuetypes.fields"
            )
            
            return {
                "issue_types": issue_types,
                "metadata": metadata
            }
        except Exception as e:
            print(f"⚠️ Ошибка при получении полей проекта: {e}")
            return {"error": str(e)}
    
    async def _get_issue_info(self, issue_key: str) -> Dict[str, Any]:
        """Получает информацию о конкретной заявке."""
        try:
            issue = await self.client.get_issue(issue_key)
            return {
                "key": issue.key,
                "summary": issue.summary,
                "description": issue.description,
                "status": issue.status,
                "assignee": issue.assignee,
                "created": issue.created.isoformat(),
                "updated": issue.updated.isoformat(),
                "raw_data": issue.raw_data
            }
        except Exception as e:
            print(f"⚠️ Ошибка при получении информации о заявке: {e}")
            return {"error": str(e)}
    
    async def _get_portal_fields(self, service_desk_url: str) -> Dict[str, Any]:
        """Получает поля Service Desk портала из HTML страницы."""
        try:
            # Добавляем заголовки браузера для имитации реального запроса
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Если есть токен, добавляем авторизацию
            if self.config.JIRA_API_TOKEN.strip():
                headers['Authorization'] = f'Bearer {self.config.JIRA_API_TOKEN}'
            
            print(f"🌐 Загружаем Service Desk портал: {service_desk_url}")
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(service_desk_url, timeout=self.config.REQUEST_TIMEOUT) as response:
                    print(f"📊 Ответ сервера: HTTP {response.status}")
                    
                    if response.status != 200:
                        print(f"⚠️ Сервер вернул ошибку: {response.status} - {response.reason}")
                        # Попробуем получить текст ошибки
                        error_text = await response.text()
                        print(f"📄 Первые 500 символов ответа: {error_text[:500]}")
                        
                        # Возвращаем базовую информацию, если есть ошибка доступа
                        return {
                            "portal_name": "Service Desk Portal (ошибка доступа)",
                            "request_type_name": "Больничный",
                            "description": f"HTTP {response.status}: {response.reason}",
                            "fields": [],
                            "error": f"HTTP {response.status}: {response.reason}"
                        }
                    
                    html = await response.text()
                    print(f"📄 Получен HTML размером: {len(html)} символов")
                    
                    # Показываем начало HTML для отладки
                    print(f"📋 Первые 200 символов HTML: {html[:200]}")
                    
                    return self._parse_portal_html(html)
        except Exception as e:
            print(f"⚠️ Ошибка при получении полей портала: {e}")
            return {
                "portal_name": "Service Desk Portal (ошибка подключения)",
                "request_type_name": "Неизвестный тип",
                "description": f"Ошибка: {str(e)}",
                "fields": [],
                "error": str(e)
            }
    
    def _parse_portal_html(self, html: str) -> Dict[str, Any]:
        """Парсит HTML страницы Service Desk и извлекает информацию о полях."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Метод 1: Пытаемся найти JSON данные в div с id="jsonPayload"
        json_payload_div = soup.find('div', id='jsonPayload')
        if json_payload_div:
            try:
                json_data = json.loads(json_payload_div.text)
                
                # Извлекаем информацию о полях
                req_create = json_data.get('reqCreate', {})
                fields = req_create.get('fields', [])
                
                portal_info = {
                    "portal_name": json_data.get('portal', {}).get('name', 'Неизвестный портал'),
                    "request_type_name": req_create.get('form', {}).get('name', 'Неизвестный тип запроса'),
                    "description": req_create.get('form', {}).get('callToAction', ''),
                    "fields": fields
                }
                
                return portal_info
                
            except json.JSONDecodeError:
                # Если JSON не удалось парсить, переходим к методу 2
                pass
        
        # Метод 2: Парсим HTML форму напрямую
        print("🔍 JSON payload не найден, парсим HTML форму напрямую...")
        
        # Показываем структуру страницы для отладки
        title_tag = soup.find('title')
        if title_tag:
            print(f"📄 Заголовок страницы: {title_tag.get_text(strip=True)}")
        
        # Ищем количество форм на странице
        forms = soup.find_all('form')
        print(f"📋 Найдено форм на странице: {len(forms)}")
        
        # Ищем поля input, select, textarea
        all_inputs = soup.find_all(['input', 'select', 'textarea'])
        print(f"🔍 Найдено полей ввода: {len(all_inputs)}")
        
        # Извлекаем заголовок формы
        portal_name = "Service Desk"
        request_type_name = "Больничный"  # Из URL видно, что это больничный
        
        # Пытаемся найти заголовок
        h1_tag = soup.find('h1')
        if h1_tag:
            request_type_name = h1_tag.get_text(strip=True)
            print(f"📋 Найден заголовок H1: {request_type_name}")
        
        # Ищем все заголовки для отладки
        headers = soup.find_all(['h1', 'h2', 'h3'])
        print(f"📄 Найдено заголовков: {[h.get_text(strip=True) for h in headers[:5]]}")
        
        # Ищем обязательные поля в форме
        required_fields = self._extract_required_fields_from_form(soup)
        print(f"🔧 Найдено обязательных полей по атрибутам: {len(required_fields)}")
        
        # Также ищем поля с ошибками валидации
        validation_errors = self._extract_validation_errors(soup)
        print(f"❌ Найдено полей с ошибками валидации: {len(validation_errors)}")
        
        # Объединяем обязательные поля
        all_fields = required_fields + validation_errors
        
        # Удаляем дубликаты по имени поля
        unique_fields = []
        seen_names = set()
        for field in all_fields:
            field_name = field.get('label', field.get('name', ''))
            if field_name not in seen_names:
                seen_names.add(field_name)
                unique_fields.append(field)
        
        print(f"✅ Итого уникальных обязательных полей: {len(unique_fields)}")
        for field in unique_fields:
            print(f"   - {field.get('label', 'Без названия')} ({field.get('fieldType', 'unknown')})")
        
        portal_info = {
            "portal_name": portal_name,
            "request_type_name": request_type_name,
            "description": "",
            "fields": unique_fields
        }
        
        return portal_info
    
    def _extract_required_fields_from_form(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Извлекает обязательные поля из HTML формы."""
        required_fields = []
        
        # Ищем поля с атрибутом required
        for field in soup.find_all(['input', 'select', 'textarea'], required=True):
            field_data = {
                "fieldId": field.get('id', field.get('name', '')),
                "label": self._get_field_label(soup, field),
                "fieldType": field.name,
                "required": True,
                "description": field.get('title', ''),
                "values": []
            }
            
            # Для select полей извлекаем опции
            if field.name == 'select':
                for option in field.find_all('option'):
                    if option.get('value'):
                        field_data["values"].append({
                            "value": option.get('value'),
                            "label": option.get_text(strip=True)
                        })
            
            required_fields.append(field_data)
        
        # Ищем поля с классом "required"
        for field in soup.find_all(['input', 'select', 'textarea'], class_=re.compile(r'required')):
            field_id = field.get('id', field.get('name', ''))
            # Проверяем, что поле еще не добавлено
            if not any(f.get('fieldId') == field_id for f in required_fields):
                field_data = {
                    "fieldId": field_id,
                    "label": self._get_field_label(soup, field),
                    "fieldType": field.name,
                    "required": True,
                    "description": field.get('title', ''),
                    "values": []
                }
                required_fields.append(field_data)
        
        return required_fields
    
    def _extract_validation_errors(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Извлекает информацию об обязательных полях из сообщений об ошибках валидации."""
        validation_fields = []
        
        # Ищем сообщения об ошибках валидации
        error_messages = soup.find_all(string=re.compile(r'Please provide a value for required field'))
        
        for error_msg in error_messages:
            # Извлекаем название поля из сообщения
            # Пример: "Please provide a value for required field 'Тип запроса'"
            match = re.search(r"Please provide a value for required field '([^']+)'", error_msg)
            if match:
                field_name = match.group(1)
                field_data = {
                    "fieldId": field_name.lower().replace(' ', '_'),
                    "label": field_name,
                    "fieldType": "unknown",
                    "required": True,
                    "description": f"Обязательное поле (определено из ошибки валидации)",
                    "values": []
                }
                validation_fields.append(field_data)
        
        # Также ищем элементы с классами ошибок
        for error_element in soup.find_all(class_=re.compile(r'error|invalid|required')):
            error_text = error_element.get_text(strip=True)
            if 'required field' in error_text:
                match = re.search(r"'([^']+)'", error_text)
                if match:
                    field_name = match.group(1)
                    if not any(f.get('label') == field_name for f in validation_fields):
                        field_data = {
                            "fieldId": field_name.lower().replace(' ', '_'),
                            "label": field_name,
                            "fieldType": "unknown",
                            "required": True,
                            "description": f"Обязательное поле (определено из ошибки валидации)",
                            "values": []
                        }
                        validation_fields.append(field_data)
        
        return validation_fields
    
    def _get_field_label(self, soup: BeautifulSoup, field) -> str:
        """Получает метку поля из HTML."""
        field_id = field.get('id')
        field_name = field.get('name')
        
        # Ищем label по for атрибуту
        if field_id:
            label = soup.find('label', for_=field_id)
            if label:
                return label.get_text(strip=True)
        
        # Ищем label по содержимому
        if field_name:
            label = soup.find('label', string=re.compile(field_name, re.IGNORECASE))
            if label:
                return label.get_text(strip=True)
        
        # Ищем ближайший label
        parent = field.parent
        while parent and parent.name != 'body':
            label = parent.find('label')
            if label:
                return label.get_text(strip=True)
            parent = parent.parent
        
        return field.get('placeholder', field.get('name', 'Неизвестное поле'))
    
    def _generate_report(
        self, 
        project_key: str, 
        project_info: Dict[str, Any], 
        project_fields: Dict[str, Any], 
        issue_info: Dict[str, Any], 
        portal_fields: Dict[str, Any],
        jira_issue_url: str,
        service_desk_url: str
    ) -> Dict[str, Any]:
        """Генерирует итоговый отчет."""
        
        # Анализируем обязательные поля из JIRA API
        system_required_fields = self._extract_system_required_fields(project_fields)
        
        # Анализируем обязательные поля из Service Desk портала
        portal_required_fields = self._extract_portal_required_fields(portal_fields)
        
        # Анализируем заполненные поля в примере
        filled_fields = self._extract_filled_fields(issue_info)
        
        report = {
            "analysis_date": datetime.now().isoformat(),
            "project_name": project_info.get('name', 'Неизвестный проект'),
            "project_key": project_key,
            "analyzed_urls": {
                "jira_issue": jira_issue_url,
                "service_desk": service_desk_url
            },
            "system_required_fields": system_required_fields,
            "portal_required_fields": portal_required_fields,
            "filled_fields_example": filled_fields,
            "automation_analysis": self._analyze_automation(filled_fields),
            "raw_data": {
                "project_info": project_info,
                "project_fields": project_fields,
                "issue_info": issue_info,
                "portal_fields": portal_fields
            }
        }
        
        return report
    
    def _extract_system_required_fields(self, project_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлекает обязательные поля из системы JIRA."""
        required_fields = []
        
        metadata = project_fields.get('metadata', {})
        projects = metadata.get('projects', [])
        
        for project in projects:
            for issue_type in project.get('issuetypes', []):
                fields = issue_type.get('fields', {})
                
                for field_id, field_info in fields.items():
                    if field_info.get('required', False):
                        field_data = {
                            "field_id": field_id,
                            "name": field_info.get('name', 'Неизвестное поле'),
                            "type": field_info.get('schema', {}).get('type', 'unknown'),
                            "issue_type": issue_type.get('name', 'Неизвестный тип'),
                            "allowed_values": []
                        }
                        
                        # Извлекаем возможные значения
                        if 'allowedValues' in field_info:
                            for value in field_info['allowedValues']:
                                if isinstance(value, dict):
                                    field_data["allowed_values"].append({
                                        "id": value.get('id', ''),
                                        "name": value.get('name', value.get('value', str(value)))
                                    })
                                else:
                                    field_data["allowed_values"].append({
                                        "id": str(value),
                                        "name": str(value)
                                    })
                        
                        required_fields.append(field_data)
        
        return required_fields
    
    def _extract_portal_required_fields(self, portal_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлекает обязательные поля из Service Desk портала."""
        required_fields = []
        
        fields = portal_fields.get('fields', [])
        
        for field in fields:
            # Проверяем, что поле является обязательным
            if field.get('required', False):
                field_data = {
                    "field_id": field.get('fieldId', field.get('label', '').lower().replace(' ', '_')),
                    "name": field.get('label', 'Неизвестное поле'),
                    "type": field.get('fieldType', 'unknown'),
                    "description": field.get('description', ''),
                    "allowed_values": []
                }
                
                # Извлекаем возможные значения
                if 'values' in field:
                    for value in field['values']:
                        field_data["allowed_values"].append({
                            "id": value.get('value', ''),
                            "name": value.get('label', '')
                        })
                
                required_fields.append(field_data)
        
        return required_fields
    
    def _extract_filled_fields(self, issue_info: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает заполненные поля из примера заявки."""
        if 'raw_data' not in issue_info:
            return {"error": "Нет данных о заявке"}
        
        raw_data = issue_info['raw_data']
        fields = raw_data.get('fields', {})
        
        filled_fields = {}
        
        for field_id, field_value in fields.items():
            if field_value is not None and field_value != "":
                # Обрабатываем разные типы полей
                if isinstance(field_value, dict):
                    if 'displayName' in field_value:
                        filled_fields[field_id] = field_value['displayName']
                    elif 'name' in field_value:
                        filled_fields[field_id] = field_value['name']
                    elif 'value' in field_value:
                        filled_fields[field_id] = field_value['value']
                    else:
                        filled_fields[field_id] = str(field_value)
                elif isinstance(field_value, list):
                    filled_fields[field_id] = [str(item) for item in field_value]
                else:
                    filled_fields[field_id] = str(field_value)
        
        return filled_fields
    
    def _analyze_automation(self, filled_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Анализирует возможную автоматизацию в заполнении полей."""
        automation_analysis = {
            "auto_filled_fields": [],
            "user_filled_fields": [],
            "system_fields": []
        }
        
        # Поля, которые обычно заполняются автоматически
        auto_fields = {
            'created': 'Дата создания',
            'updated': 'Дата обновления',
            'creator': 'Создатель',
            'reporter': 'Заявитель',
            'labels': 'Метки (могут добавляться автоматически)',
            'project': 'Проект',
            'issuetype': 'Тип задачи',
            'status': 'Статус',
            'priority': 'Приоритет (может быть по умолчанию)'
        }
        
        # Системные поля
        system_field_prefixes = ['customfield_', 'resolution', 'worklog', 'attachment']
        
        for field_id, field_value in filled_fields.items():
            if field_id in auto_fields:
                automation_analysis["auto_filled_fields"].append({
                    "field_id": field_id,
                    "description": auto_fields[field_id],
                    "value": field_value
                })
            elif any(field_id.startswith(prefix) for prefix in system_field_prefixes):
                automation_analysis["system_fields"].append({
                    "field_id": field_id,
                    "value": field_value
                })
            else:
                automation_analysis["user_filled_fields"].append({
                    "field_id": field_id,
                    "value": field_value
                })
        
        return automation_analysis
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Сохраняет отчет в файл."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jira_analysis_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        return filename
    
    def generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Генерирует отчет в формате Markdown."""
        md_content = f"""# Анализ проекта JIRA: {report['project_name']} ({report['project_key']})

**Дата анализа:** {report['analysis_date']}

## Анализируемые ссылки

- **Заявка JIRA:** {report['analyzed_urls']['jira_issue']}
- **Service Desk портал:** {report['analyzed_urls']['service_desk']}

## 1. Название проекта

**{report['project_name']}** (ключ: {report['project_key']})

## 2. Обязательные поля в системе JIRA

"""
        
        for field in report['system_required_fields']:
            md_content += f"### {field['name']} (`{field['field_id']}`)\n"
            md_content += f"- **Тип:** {field['type']}\n"
            md_content += f"- **Тип задачи:** {field['issue_type']}\n"
            
            if field['allowed_values']:
                md_content += "- **Возможные значения:**\n"
                for value in field['allowed_values']:
                    md_content += f"  - {value['name']} (ID: {value['id']})\n"
            
            md_content += "\n"
        
        md_content += "## 3. Обязательные поля на портале Service Desk\n\n"
        
        for field in report['portal_required_fields']:
            md_content += f"### {field['name']} (`{field['field_id']}`)\n"
            md_content += f"- **Тип:** {field['type']}\n"
            
            if field['description']:
                md_content += f"- **Описание:** {field['description']}\n"
            
            if field['allowed_values']:
                md_content += "- **Возможные значения:**\n"
                for value in field['allowed_values']:
                    md_content += f"  - {value['name']} (ID: {value['id']})\n"
            
            md_content += "\n"
        
        md_content += "## 4. Заполненные поля в примере\n\n"
        
        automation = report['automation_analysis']
        
        if automation['auto_filled_fields']:
            md_content += "### Автоматически заполненные поля\n\n"
            for field in automation['auto_filled_fields']:
                md_content += f"- **{field['field_id']}:** {field['description']} = `{field['value']}`\n"
            md_content += "\n"
        
        if automation['user_filled_fields']:
            md_content += "### Поля, заполненные пользователем\n\n"
            for field in automation['user_filled_fields']:
                md_content += f"- **{field['field_id']}:** `{field['value']}`\n"
            md_content += "\n"
        
        if automation['system_fields']:
            md_content += "### Системные поля\n\n"
            for field in automation['system_fields']:
                md_content += f"- **{field['field_id']}:** `{field['value']}`\n"
            md_content += "\n"
        
        return md_content


# ============================================================================
# ОСНОВНЫЕ ФУНКЦИИ
# ============================================================================

async def analyze_jira_project(jira_issue_url: str, service_desk_url: str) -> Dict[str, Any]:
    """
    Основная функция для анализа проекта JIRA.
    
    Args:
        jira_issue_url: Ссылка на заявку в JIRA
        service_desk_url: Ссылка на создание заявки в Service Desk
        
    Returns:
        Dict с результатами анализа
    """
    config = LocalJiraConfig()
    
    # Показываем статус конфигурации
    print(f"⚙️ Статус конфигурации: {config.get_status_message()}")
    if not config.is_configured():
        print("💡 Для полного анализа нужен API токен в .env файле:")
        print("   JIRA_API_TOKEN=ваш_токен_здесь")
        print("   Получить токен: https://jira.petrovich.tech/secure/ViewProfile.jspa")
        print()
    
    analyzer = JiraAnalyzer(config)
    
    try:
        report = await analyzer.analyze_urls(jira_issue_url, service_desk_url)
        
        # Сохраняем отчет в JSON
        json_filename = analyzer.save_report(report)
        print(f"📄 JSON отчет сохранен: {json_filename}")
        
        # Генерируем Markdown отчет
        markdown_content = analyzer.generate_markdown_report(report)
        md_filename = json_filename.replace('.json', '.md')
        
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"📝 Markdown отчет сохранен: {md_filename}")
        
        # Показываем краткую статистику
        print(f"\n📊 Результаты анализа:")
        print(f"   🏢 Проект: {report['project_name']} ({report['project_key']})")
        print(f"   🔧 Обязательных полей в системе: {len(report['system_required_fields'])}")
        print(f"   🌐 Обязательных полей на портале: {len(report['portal_required_fields'])}")
        
        # Анализ автоматизации
        automation = report['automation_analysis']
        filled_count = len(report.get('filled_fields_example', {}))
        if isinstance(report.get('filled_fields_example'), dict) and 'error' not in report['filled_fields_example']:
            print(f"   📝 Заполненных полей в примере: {filled_count}")
            print(f"   🤖 Автоматически заполненных: {len(automation['auto_filled_fields'])}")
            print(f"   👤 Заполненных пользователем: {len(automation['user_filled_fields'])}")
            print(f"   ⚙️ Системных полей: {len(automation['system_fields'])}")
        
        return report
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        if "403" in str(e) or "401" in str(e):
            print("💡 Возможно, нужен валидный API токен в .env файле")
        raise


if __name__ == "__main__":
    import sys
    
    # Дефолтные ссылки (доступные заявки из проекта SCHED)
    DEFAULT_JIRA_ISSUE_URL = "@https://jira.petrovich.tech/browse/SCHED-144766"
    DEFAULT_SERVICE_DESK_URL = "@https://jira.petrovich.tech/servicedesk/customer/portal/55/create/926"
    
    # Определяем ссылки
    if len(sys.argv) == 3:
        # Используем переданные аргументы
        jira_url = sys.argv[1]
        service_desk_url = sys.argv[2]
        print("🔗 Используем переданные ссылки:")
    elif len(sys.argv) == 1:
        # Используем дефолтные ссылки
        jira_url = DEFAULT_JIRA_ISSUE_URL
        service_desk_url = DEFAULT_SERVICE_DESK_URL
        print("🔗 Используем дефолтные ссылки:")
    else:
        print("❌ Использование:")
        print("  python jira_analyzer.py                                              # использовать дефолтные ссылки")
        print("  python jira_analyzer.py <jira_issue_url> <service_desk_url>         # использовать свои ссылки")
        print()
        print("🔗 Дефолтные ссылки:")
        print(f"  Заявка JIRA: {DEFAULT_JIRA_ISSUE_URL}")
        print(f"  Service Desk: {DEFAULT_SERVICE_DESK_URL}")
        print(f"  (Используются доступные заявки из проекта SCHED)")
        sys.exit(1)
    
    print(f"  📋 Заявка JIRA: {jira_url}")
    print(f"  🌐 Service Desk: {service_desk_url}")
    print()
    
    try:
        asyncio.run(analyze_jira_project(jira_url, service_desk_url))
    except KeyboardInterrupt:
        print("\n⏹️ Анализ прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1) 