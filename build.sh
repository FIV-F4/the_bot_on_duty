#!/bin/bash

# Создаем виртуальное окружение
python3 -m venv venv

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Создаем исполняемый файл
pyinstaller --onefile \
            --add-data "config.json:." \
            --add-data "data:data" \
            --hidden-import=aiogram \
            --hidden-import=selenium \
            --hidden-import=webdriver_manager \
            --hidden-import=python_dotenv \
            --hidden-import=requests \
            main.py

# Деактивируем виртуальное окружение
deactivate

echo "Сборка завершена. Исполняемый файл находится в папке dist/" 