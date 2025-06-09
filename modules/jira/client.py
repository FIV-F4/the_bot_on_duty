"""
Клиент для работы с Jira API
"""
import logging
from typing import Dict, Any

from jira import JIRA
from utils.config import CONFIG

logger = logging.getLogger(__name__)

def create_failure_issue(data: Dict[str, Any]) -> str:
    """
    Создает задачу в Jira
    
    Args:
        data: Данные для создания задачи
        
    Returns:
        str: Ключ созданной задачи
    """
    try:
        jira = JIRA(
            server=CONFIG["JIRA"]["LOGIN_URL"],
            basic_auth=(CONFIG["JIRA"]["USERNAME"], CONFIG["JIRA"]["PASSWORD"])
        )
        
        issue_dict = {
            'project': {'key': 'FA'},
            'summary': data['summary'],
            'description': data['description'],
            'issuetype': {'name': 'Failure'},
            'customfield_10001': data.get('level', ''),
            'customfield_10002': data.get('service', ''),
            'customfield_10003': data.get('naumen_type', ''),
            'customfield_10004': data.get('stream_1c', ''),
            'customfield_10005': data.get('influence', '')
        }
        
        new_issue = jira.create_issue(fields=issue_dict)
        logger.info(f"Создана задача {new_issue.key}")
        return new_issue.key
        
    except Exception as e:
        logger.error(f"Ошибка при создании задачи в Jira: {str(e)}")
        raise 