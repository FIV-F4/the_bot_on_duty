"""
Пример использования анализатора JIRA.
"""

import asyncio
from jira_analyzer import analyze_jira_project


async def main():
    """Пример анализа проекта JIRA."""
    
    # Ссылки для анализа (доступные заявки из проекта SCHED)
    jira_issue_url = "@https://jira.petrovich.tech/browse/SCHED-144766"
    service_desk_url = "@https://jira.petrovich.tech/servicedesk/customer/portal/55/create/926"
    
    print("🚀 Запуск анализа проекта JIRA...")
    print()
    
    try:
        # Выполняем анализ
        report = await analyze_jira_project(jira_issue_url, service_desk_url)
        
        print("\n✅ Анализ завершен успешно!")
        print(f"📊 Проект: {report['project_name']} ({report['project_key']})")
        
        # Показываем краткую статистику
        system_fields = len(report.get('system_required_fields', []))
        portal_fields = len(report.get('portal_required_fields', []))
        
        print(f"🔧 Обязательных полей в системе: {system_fields}")
        print(f"🌐 Обязательных полей на портале: {portal_fields}")
        
        # Анализ автоматизации
        automation = report.get('automation_analysis', {})
        if automation:
            auto_fields = len(automation.get('auto_filled_fields', []))
            user_fields = len(automation.get('user_filled_fields', []))
            sys_fields = len(automation.get('system_fields', []))
            
            print(f"🤖 Автоматически заполненных полей: {auto_fields}")
            print(f"👤 Заполненных пользователем: {user_fields}")
            print(f"⚙️ Системных полей: {sys_fields}")
        
        return report
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(main()) 