import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATE_FILE = "data/state.json"

if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            logger.info("🔄 Файл state.json валиден, пересохраняем")
            with open(STATE_FILE, "w") as f:
                json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"❌ Файл повреждён: {e}. Пересоздаём.")
else:
    logger.info("🆕 Файл state.json не найден. Создаём новый.")

with open(STATE_FILE, "w") as f:
    json.dump({"active_alarms": {}, "active_maintenances": {}, "user_states": {}}, f, indent=2)

print("✅ Файл состояния пересоздан")