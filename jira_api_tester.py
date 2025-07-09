#!/usr/bin/env python3
"""
JIRA API Тестер - GUI приложение для отправки произвольных запросов к JIRA API.

Использует авторизацию из конфигурации проекта.
Позволяет отправлять любые HTTP запросы с JSON телом и просматривать ответы.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import requests
import traceback
from pathlib import Path
import sys
import os
from typing import Dict, Any, Optional

# Добавляем путь к проекту для импорта конфигурации
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from common.jira.config import JiraConfig
    HAS_CONFIG = True
except Exception as e:
    print(f"⚠️ Не удалось загрузить конфигурацию проекта: {e}")
    print("Используется базовая авторизация")
    HAS_CONFIG = False


class JiraApiTester:
    """GUI приложение для тестирования JIRA API."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("JIRA API Тестер")
        self.root.geometry("900x700")
        
        # Загружаем конфигурацию
        self.config = self._load_config()
        
        # Создаем интерфейс
        self._create_widgets()
        
        # Заполняем дефолтные значения
        self._set_defaults()
    
    def _load_config(self) -> Optional[JiraConfig]:
        """Загружает конфигурацию JIRA из проекта."""
        if not HAS_CONFIG:
            return None
            
        try:
            config = JiraConfig()
            return config
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфигурации: {e}")
            return None
    
    def _create_widgets(self):
        """Создает виджеты интерфейса."""
        # Главный фрейм с прокруткой
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === СЕКЦИЯ КОНФИГУРАЦИИ ===
        config_frame = ttk.LabelFrame(main_frame, text="🔧 Конфигурация", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Статус конфигурации
        self.config_status = ttk.Label(config_frame, text="", foreground="green")
        self.config_status.pack(anchor=tk.W)
        
        # === СЕКЦИЯ ЗАПРОСА ===
        request_frame = ttk.LabelFrame(main_frame, text="📤 HTTP Запрос", padding=10)
        request_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # HTTP метод
        method_frame = ttk.Frame(request_frame)
        method_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(method_frame, text="HTTP метод:").pack(side=tk.LEFT)
        self.method_var = tk.StringVar(value="GET")
        method_combo = ttk.Combobox(method_frame, textvariable=self.method_var, 
                                  values=["GET", "POST", "PUT", "DELETE"], 
                                  state="readonly", width=10)
        method_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # URL
        url_frame = ttk.Frame(request_frame)
        url_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(url_frame, text="URL:").pack(anchor=tk.W)
        self.url_entry = tk.Entry(url_frame, font=("Consolas", 10))
        self.url_entry.pack(fill=tk.X, pady=(2, 0))
        
        # Привязываем горячие клавиши для URL поля
        self._bind_hotkeys(self.url_entry)
        
        # JSON тело запроса
        ttk.Label(request_frame, text="JSON тело запроса:").pack(anchor=tk.W, pady=(10, 2))
        self.json_text = scrolledtext.ScrolledText(request_frame, height=8, 
                                                 font=("Consolas", 10))
        self.json_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Привязываем горячие клавиши для JSON поля
        self._bind_hotkeys(self.json_text)
        
        # Кнопки
        button_frame = ttk.Frame(request_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="🚀 Отправить запрос", 
                  command=self._send_request).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="🧹 Очистить", 
                  command=self._clear_all).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(button_frame, text="📋 Примеры", 
                  command=self._show_examples).pack(side=tk.LEFT, padx=(5, 0))
        
        # === СЕКЦИЯ ОТВЕТА ===
        response_frame = ttk.LabelFrame(main_frame, text="📥 Ответ API", padding=10)
        response_frame.pack(fill=tk.BOTH, expand=True)
        
        # Информация о статусе
        self.status_label = ttk.Label(response_frame, text="Готов к отправке запроса", 
                                    foreground="gray")
        self.status_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Ответ
        self.response_text = scrolledtext.ScrolledText(response_frame, height=12, 
                                                     font=("Consolas", 9))
        self.response_text.pack(fill=tk.BOTH, expand=True)
        
        # Привязываем горячие клавиши для поля ответа
        self._bind_hotkeys(self.response_text)
    
    def _bind_hotkeys(self, widget):
        """Привязывает горячие клавиши к виджету."""
        # Стандартные горячие клавиши
        widget.bind('<Control-v>', lambda e: self._paste_text(widget))
        widget.bind('<Control-V>', lambda e: self._paste_text(widget))
        widget.bind('<Control-c>', lambda e: self._copy_text(widget))
        widget.bind('<Control-C>', lambda e: self._copy_text(widget))
        widget.bind('<Control-a>', lambda e: self._select_all(widget))
        widget.bind('<Control-A>', lambda e: self._select_all(widget))
        widget.bind('<Control-x>', lambda e: self._cut_text(widget))
        widget.bind('<Control-X>', lambda e: self._cut_text(widget))
        
        # Контекстное меню по правой кнопке мыши
        widget.bind('<Button-3>', lambda e: self._show_context_menu(e, widget))
    
    def _paste_text(self, widget):
        """Вставляет текст из буфера обмена."""
        try:
            clipboard_text = self.root.clipboard_get()
            if hasattr(widget, 'insert'):
                if isinstance(widget, tk.Entry):
                    # Для Entry виджета
                    widget.insert(tk.INSERT, clipboard_text)
                else:
                    # Для Text виджета
                    widget.insert(tk.INSERT, clipboard_text)
        except tk.TclError:
            # Буфер обмена пуст или недоступен
            pass
        return 'break'  # Предотвращаем стандартную обработку
    
    def _copy_text(self, widget):
        """Копирует выделенный текст в буфер обмена."""
        try:
            if isinstance(widget, tk.Entry):
                if widget.selection_present():
                    selected_text = widget.selection_get()
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected_text)
            else:
                # Для Text виджета
                try:
                    selected_text = widget.selection_get()
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected_text)
                except tk.TclError:
                    # Нет выделения
                    pass
        except tk.TclError:
            pass
        return 'break'
    
    def _cut_text(self, widget):
        """Вырезает выделенный текст в буфер обмена."""
        try:
            if isinstance(widget, tk.Entry):
                if widget.selection_present():
                    selected_text = widget.selection_get()
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected_text)
                    widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                # Для Text виджета
                try:
                    selected_text = widget.selection_get()
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected_text)
                    widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                except tk.TclError:
                    # Нет выделения
                    pass
        except tk.TclError:
            pass
        return 'break'
    
    def _select_all(self, widget):
        """Выделяет весь текст в виджете."""
        if isinstance(widget, tk.Entry):
            widget.select_range(0, tk.END)
        else:
            # Для Text виджета
            widget.tag_add(tk.SEL, "1.0", tk.END)
        return 'break'
    
    def _show_context_menu(self, event, widget):
        """Показывает контекстное меню."""
        context_menu = tk.Menu(self.root, tearoff=0)
        
        # Добавляем пункты меню
        context_menu.add_command(label="📋 Вставить (Ctrl+V)", 
                               command=lambda: self._paste_text(widget))
        context_menu.add_command(label="📄 Копировать (Ctrl+C)", 
                               command=lambda: self._copy_text(widget))
        context_menu.add_command(label="✂️ Вырезать (Ctrl+X)", 
                               command=lambda: self._cut_text(widget))
        context_menu.add_separator()
        context_menu.add_command(label="🔤 Выделить все (Ctrl+A)", 
                               command=lambda: self._select_all(widget))
        
        # Специальные функции для JSON поля
        if widget == self.json_text:
            context_menu.add_separator()
            context_menu.add_command(label="🎨 Форматировать JSON", 
                                   command=lambda: self._format_json())
            context_menu.add_command(label="🧹 Очистить JSON", 
                                   command=lambda: self.json_text.delete(1.0, tk.END))
        
        # Показываем меню в позиции курсора
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _format_json(self):
        """Форматирует JSON в поле ввода."""
        try:
            json_text = self.json_text.get(1.0, tk.END).strip()
            if json_text:
                parsed = json.loads(json_text)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                self.json_text.delete(1.0, tk.END)
                self.json_text.insert(1.0, formatted)
        except json.JSONDecodeError as e:
            messagebox.showerror("Ошибка JSON", f"Некорректный JSON:\n{str(e)}")

    def _set_defaults(self):
        """Устанавливает значения по умолчанию."""
        # Показываем статус конфигурации
        if self.config:
            self.config_status.config(text=f"✅ Подключено к: {self.config.JIRA_URL}", 
                                    foreground="green")
            # Устанавливаем базовый URL
            base_url = f"{self.config.JIRA_URL}/rest/api/{self.config.API_VERSION}"
            self.url_entry.insert(0, f"{base_url}/issue/SCHED-144766")
        else:
            self.config_status.config(text="❌ Конфигурация не загружена", 
                                    foreground="red")
            self.url_entry.insert(0, "https://jira.petrovich.tech/rest/api/2/issue/SCHED-144766")
        
        # Пример JSON для POST запроса
        example_json = {
            "fields": {
                "project": {"key": "TEST"},
                "summary": "Тестовая задача",
                "description": "Создано через API тестер",
                "issuetype": {"name": "Task"}
            }
        }
        self.json_text.insert(tk.END, json.dumps(example_json, indent=2, ensure_ascii=False))
    
    def _get_headers(self) -> Dict[str, str]:
        """Формирует заголовки для запроса."""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'JIRA-API-Tester/1.0'
        }
        
        # Добавляем авторизацию из конфигурации
        if self.config and hasattr(self.config, 'JIRA_API_TOKEN'):
            headers['Authorization'] = f'Bearer {self.config.JIRA_API_TOKEN}'
        else:
            # Если нет конфигурации, предупреждаем пользователя
            messagebox.showwarning("Предупреждение", 
                                 "Авторизация не настроена!\n"
                                 "Запрос будет отправлен без токена.")
        
        return headers
    
    def _send_request(self):
        """Отправляет HTTP запрос к JIRA API."""
        try:
            # Получаем данные из интерфейса
            method = self.method_var.get()
            url = self.url_entry.get().strip()
            json_data = self.json_text.get(1.0, tk.END).strip()
            
            # Валидация
            if not url:
                messagebox.showerror("Ошибка", "Укажите URL для запроса")
                return
            
            # Парсим JSON если есть
            request_data = None
            if json_data:
                try:
                    request_data = json.loads(json_data)
                except json.JSONDecodeError as e:
                    messagebox.showerror("Ошибка JSON", f"Некорректный JSON:\n{str(e)}")
                    return
            
            # Обновляем статус
            self.status_label.config(text=f"🔄 Отправляем {method} запрос...", 
                                   foreground="blue")
            self.root.update()
            
            # Отправляем запрос
            headers = self._get_headers()
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=request_data if method in ['POST', 'PUT'] else None,
                timeout=30
            )
            
            # Обрабатываем ответ
            self._display_response(response)
            
        except requests.exceptions.Timeout:
            self._display_error("⏰ Таймаут запроса (30 сек)")
        except requests.exceptions.ConnectionError:
            self._display_error("🔌 Ошибка подключения к серверу")
        except Exception as e:
            self._display_error(f"❌ Ошибка: {str(e)}\n\n{traceback.format_exc()}")
    
    def _display_response(self, response: requests.Response):
        """Отображает ответ от API."""
        # Обновляем статус
        status_color = "green" if 200 <= response.status_code < 300 else "red"
        self.status_label.config(
            text=f"📡 Ответ: {response.status_code} {response.reason}", 
            foreground=status_color
        )
        
        # Очищаем область ответа
        self.response_text.delete(1.0, tk.END)
        
        # Выводим информацию о запросе
        self.response_text.insert(tk.END, f"🔗 URL: {response.url}\n")
        self.response_text.insert(tk.END, f"📊 Статус: {response.status_code} {response.reason}\n")
        self.response_text.insert(tk.END, f"⏱️ Время: {response.elapsed.total_seconds():.2f} сек\n")
        self.response_text.insert(tk.END, f"📏 Размер: {len(response.content)} байт\n\n")
        
        # Заголовки ответа
        self.response_text.insert(tk.END, "📋 Заголовки ответа:\n")
        for header, value in response.headers.items():
            self.response_text.insert(tk.END, f"  {header}: {value}\n")
        self.response_text.insert(tk.END, "\n")
        
        # Тело ответа
        self.response_text.insert(tk.END, "📄 Тело ответа:\n")
        try:
            # Пытаемся отформатировать как JSON
            if response.headers.get('content-type', '').startswith('application/json'):
                json_data = response.json()
                formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
                self.response_text.insert(tk.END, formatted_json)
            else:
                # Обычный текст
                self.response_text.insert(tk.END, response.text)
        except:
            # Если не получается, выводим как есть
            self.response_text.insert(tk.END, response.text)
    
    def _display_error(self, error_message: str):
        """Отображает ошибку."""
        self.status_label.config(text="❌ Ошибка выполнения запроса", 
                               foreground="red")
        
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, error_message)
    
    def _clear_all(self):
        """Очищает все поля."""
        self.url_entry.delete(0, tk.END)
        self.json_text.delete(1.0, tk.END)
        self.response_text.delete(1.0, tk.END)
        self.status_label.config(text="Готов к отправке запроса", foreground="gray")
    
    def _show_examples(self):
        """Показывает примеры запросов."""
        examples_window = tk.Toplevel(self.root)
        examples_window.title("📚 Примеры запросов")
        examples_window.geometry("600x500")
        
        notebook = ttk.Notebook(examples_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        examples = {
            "Получить задачу": {
                "method": "GET",
                "url": "/rest/api/2/issue/SCHED-144766",
                "json": ""
            },
            "Создать задачу": {
                "method": "POST", 
                "url": "/rest/api/2/issue",
                "json": {
                    "fields": {
                        "project": {"key": "SCHED"},
                        "summary": "Тестовая задача из API",
                        "description": "Создано через JIRA API Тестер",
                        "issuetype": {"name": "Task"}
                    }
                }
            },
            "Получить проекты": {
                "method": "GET",
                "url": "/rest/api/2/project",
                "json": ""
            },
            "Service Desk запрос": {
                "method": "POST",
                "url": "/rest/servicedeskapi/request",
                "json": {
                    "serviceDeskId": "55",
                    "requestTypeId": "926", 
                    "requestFieldValues": {
                        "summary": "Тест через Service Desk API",
                        "description": "Тестовый запрос"
                    }
                }
            },
            "Поиск задач": {
                "method": "POST",
                "url": "/rest/api/2/search",
                "json": {
                    "jql": "project = SCHED AND status != Закрыта",
                    "maxResults": 5,
                    "fields": ["summary", "status", "assignee"]
                }
            }
        }
        
        for name, example in examples.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=name)
            
            # Информация
            info_frame = ttk.Frame(frame)
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(info_frame, text=f"Метод: {example['method']}", 
                     font=("Arial", 10, "bold")).pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"URL: {example['url']}", 
                     font=("Consolas", 9)).pack(anchor=tk.W)
            
            # JSON
            if example['json']:
                ttk.Label(frame, text="JSON тело:").pack(anchor=tk.W, padx=10, pady=(10, 2))
                json_text = scrolledtext.ScrolledText(frame, height=15, font=("Consolas", 9))
                json_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
                json_text.insert(tk.END, json.dumps(example['json'], indent=2, ensure_ascii=False))
                json_text.config(state=tk.DISABLED)
            
            # Кнопка применения
            ttk.Button(frame, text="📋 Использовать этот пример", 
                      command=lambda e=example: self._apply_example(e, examples_window)).pack(pady=10)
    
    def _apply_example(self, example: Dict[str, Any], window: tk.Toplevel):
        """Применяет пример запроса."""
        # Метод
        self.method_var.set(example['method'])
        
        # URL
        self.url_entry.delete(0, tk.END)
        base_url = self.config.JIRA_URL if self.config else "https://jira.petrovich.tech"
        full_url = base_url + example['url']
        self.url_entry.insert(0, full_url)
        
        # JSON
        self.json_text.delete(1.0, tk.END)
        if example['json']:
            self.json_text.insert(tk.END, json.dumps(example['json'], indent=2, ensure_ascii=False))
        
        # Закрываем окно примеров
        window.destroy()
        
        # Фокус на главное окно
        self.root.focus_force()


def main():
    """Основная функция приложения."""
    try:
        root = tk.Tk()
        app = JiraApiTester(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Приложение закрыто пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main() 