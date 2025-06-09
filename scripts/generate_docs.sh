#!/bin/bash

# Активация виртуального окружения
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements-dev.txt

# Генерация документации
cd docs
sphinx-apidoc -o source/api ../bots
sphinx-apidoc -o source/api ../application
sphinx-apidoc -o source/api ../domain
sphinx-apidoc -o source/api ../infrastructure
sphinx-apidoc -o source/api ../core

# Сборка документации
make html

echo "Документация сгенерирована в docs/build/html/" 