# config.py
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional

# Загрузка переменных окружения из .env файла
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    raise FileNotFoundError(f"Файл .env не найден в {env_path}. Создайте его и добавьте необходимые переменные.")
load_dotenv(dotenv_path=env_path)

# Базовые настройки проекта
BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"

# Telegram Bot настройки
BOT_TOKEN: Optional[str] = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения. Проверьте файл .env")

# Администраторы бота
ADMIN_ID_STR = os.getenv("ADMIN_ID", "")
ADMIN_ID: List[int] = [int(admin_id.strip()) for admin_id in ADMIN_ID_STR.split(",") if admin_id.strip()] if ADMIN_ID_STR else []

# Google Sheets настройки
SPREADSHEET_ID: str = os.getenv("SPREADSHEET_ID", "1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w")
GOOGLE_SHEETS_CREDENTIALS: Path = CREDENTIALS_FILE

if not CREDENTIALS_FILE.exists():
    raise FileNotFoundError(f"Файл credentials.json не найден в {CREDENTIALS_FILE}. Поместите его в корневую директорию.")

# Настройки логирования
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()
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
LISTINGS_SHEET_NAME = os.getenv("PROPERTIES_SHEET_NAME", "Listings")
REQUESTS_SHEET_NAME = os.getenv("REQUESTS_SHEET_NAME", "Requests")

# Настройки для retry логики
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # секунды

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