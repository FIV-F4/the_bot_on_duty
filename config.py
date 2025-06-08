# config.py

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

CONFIG_FILE = "config.json"

# Списки опций
PROBLEM_LEVELS = [
    "Замедление работы сервиса",
    "Полная недоступность сервиса",
    "Частичная недоступность сервиса",
    "Проблемы в работе сервиса",
    "Потенциальная недоступность сервиса"
]

PROBLEM_SERVICES = [
    "Naumen", "Электронная почта", "УТЦ", "УТ Юнион", "1С УТ СПБ", "1С УТ СЗФО",
    "1С УТ МСК", "1С ЦФС", "УТ СПБ+УТ СЗФО+ УТ МСК", "LMS", "Проблема с обменами",
    "Сеть и интернет 1 подразделения", "Удалённый рабочий стол RDP (trm)",
    "Удалённый рабочий стол RDP для КЦ (retrm)", "VPN офисный", "VPN ДО КЦ",
    "Стационарная телефония", "Мобильная телефония", "Сетевое хранилище (Диск Х)",
    "Сайт Petrovich.ru", "Чат на сайте", "Jira", "Confluence", "Petlocal.ru",
    "Электроэнергия", "Телеопти/Май тайм", "Сервис оплаты", "Jira + Confluence",
    "b2b.stdp.ru", "Skype for business(Lync)", "DocsVision (DV)", "УТ СПБ",
    "ЗУП", "HR-Link", "WMS", "Мобильное приложение", "Другое"
]

INFLUENCE_OPTIONS = ["Клиенты", "Бизнес-функция", "Сотрудники"]

def load_config() -> Dict[str, Any]:
    logger.info("⚙️ Загружаю конфигурацию")

    if not os.path.exists(CONFIG_FILE):
        logger.warning("❌ Конфиг не найден, создаю шаблон")
        default_config = {
            "CONFLUENCE": {
                "LOGIN_URL": "https://confluence.petrovich.tech/login.action ",
                "TARGET_URL": "https://confluence.petrovich.tech/pages/viewpage.action?pageId=309867053 ",
                "USERNAME": os.getenv("CONFLUENCE_USERNAME", ""),
                "PASSWORD": os.getenv("CONFLUENCE_PASSWORD", "")
            },
            "TELEGRAM": {
                "TOKEN": os.getenv("TELEGRAM_TOKEN", ""),
                "ALARM_CHANNEL_ID": os.getenv("ALARM_CHANNEL_ID", ""),
                "SCM_CHANNEL_ID": os.getenv("SCM_CHANNEL_ID", ""),
                "ADMIN_IDS": [
                    int(id_.strip()) for id_ in os.getenv("ADMIN_IDS", "").split(",") if id_.strip()
                ],
                "SUPERADMIN_IDS": [
                    int(id_.strip()) for id_ in os.getenv("SUPERADMIN_IDS", "").split(",") if id_.strip()
                ]
            },
            "JIRA": {
                "LOGIN_URL": "https://jira.petrovich.tech/login.jsp ",
                "USERNAME": os.getenv("JIRA_USERNAME", ""),
                "PASSWORD": os.getenv("JIRA_PASSWORD", "")
            }
        }

        # Логирование базовой конфигурации
        logger.debug("📄 Базовая конфигурация создана:")
        logger.debug(f"🔑 TELEGRAM: TOKEN={'*' * len(default_config['TELEGRAM']['TOKEN']) if default_config['TELEGRAM']['TOKEN'] else 'отсутствует'}")
        logger.debug(f"👥 ADMIN_IDS: {default_config['TELEGRAM']['ADMIN_IDS']}")
        logger.debug(f"🕵️ SUPERADMIN_IDS: {default_config['TELEGRAM']['SUPERADMIN_IDS']}")
        logger.debug(f"🔗 CONFLUENCE URL: {default_config['CONFLUENCE']['TARGET_URL']}")
        logger.debug(f"🔗 JIRA URL: {default_config['JIRA']['LOGIN_URL']}")

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
            logger.info("📝 Шаблон конфига создан")
        except Exception as e:
            logger.critical(f"❌ Не удалось создать файл конфига: {e}")
            raise

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.info("✅ Конфиг загружен")
        return config
    except json.JSONDecodeError as je:
        logger.critical(f"❌ Ошибка формата JSON в конфиге: {je}")
        raise
    except Exception as e:
        logger.critical(f"❌ Не удалось загрузить конфиг: {e}", exc_info=True)
        raise


CONFIG = load_config()


def is_admin(user_id: int) -> bool:
    return user_id in CONFIG.get("TELEGRAM", {}).get("ADMIN_IDS", [])


def is_superadmin(user_id: int) -> bool:
    superadmins = CONFIG.get("TELEGRAM", {}).get("SUPERADMIN_IDS", [])
    return user_id in superadmins