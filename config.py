"""
Конфигурация риэлторского бота.
Содержит все настройки проекта, включая Telegram, Google Sheets и логирование.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional

# Загрузка переменных окружения из .env файла
load_dotenv()

# Базовые настройки проекта
BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"

# Telegram Bot настройки
BOT_TOKEN: Optional[str] = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения. Проверьте файл .env")

# Администраторы бота (поддержка множественных админов)
ADMIN_ID_STR = os.getenv("ADMIN_ID", "")
ADMIN_ID: List[int] = []
if ADMIN_ID_STR:
    try:
        # Поддержка как одного админа, так и списка (разделенного запятыми)
        admin_ids = [int(admin_id.strip()) for admin_id in ADMIN_ID_STR.split(",") if admin_id.strip()]
        ADMIN_ID = admin_ids
    except ValueError:
        raise ValueError("ADMIN_ID должен содержать корректные числовые ID, разделенные запятыми")

# Google Sheets настройки
SPREADSHEET_ID: str = os.getenv("SPREADSHEET_ID", "1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w")
GOOGLE_SHEETS_CREDENTIALS: Path = CREDENTIALS_FILE

# Проверка существования файла credentials
if not CREDENTIALS_FILE.exists():
    raise FileNotFoundError(
        f"Файл credentials.json не найден в {CREDENTIALS_FILE}. "
        f"Поместите файл в корневую директорию проекта."
    )

# Настройки логирования
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()  # Исправлено на LOGGING_LEVEL
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

# Настройки базы данных для логов действий пользователей
DATABASE_FILE = BASE_DIR / "user_actions.db"

# Настройки валидации
MAX_NAME_LENGTH = 100
MAX_COMMENT_LENGTH = 1000
SUPPORTED_IMAGE_FORMATS = ('.jpg', '.jpeg', '.png', '.webp')

# Настройки Google Sheets API
GOOGLE_SHEETS_SCOPE = [
    "https://spreadsheets.google.com/feeds", 
    "https://www.googleapis.com/auth/drive"
]

# Названия листов в Google Sheets
LISTINGS_SHEET_NAME = os.getenv("PROPERTIES_SHEET_NAME", "Listings")  # Исправлено на PROPERTIES_SHEET_NAME
REQUESTS_SHEET_NAME = os.getenv("REQUESTS_SHEET_NAME", "Requests")

# Настройки для retry логики при работе с внешними API
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # секунды

# Функция для проверки конфигурации при запуске
def validate_config() -> None:
    """
    Проверяет корректность всех настроек конфигурации.
    Вызывает исключения при обнаружении проблем.
    """
    required_vars = {
        "BOT_TOKEN": BOT_TOKEN,
        "SPREADSHEET_ID": SPREADSHEET_ID,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
    
    if not ADMIN_ID:
        print("ПРЕДУПРЕЖДЕНИЕ: Не указан ADMIN_ID. Административные функции будут недоступны.")
    
    print(f"✓ Конфигурация успешно загружена")
    print(f"✓ Найдено администраторов: {len(ADMIN_ID)}")
    print(f"✓ Файл credentials.json: {'найден' if CREDENTIALS_FILE.exists() else 'НЕ НАЙДЕН'}")