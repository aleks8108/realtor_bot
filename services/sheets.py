

import time
import logging
from typing import Dict, Any, List, Optional
from google.oauth2.service_account import Credentials
from gspread import authorize, Spreadsheet
import gspread
from googleapiclient.discovery import build
from exceptions.custom_exceptions import GoogleSheetsError, ServiceError
import aiohttp
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import asyncio

logger = logging.getLogger(__name__)

SPREADSHEET_ID = '1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w'

class GoogleSheetsService:
    def __init__(self):
        self._client: Optional[authorize] = None
        self._spreadsheet: Optional[Spreadsheet] = None
        self._lock = asyncio.Lock()  # Для синхронизации доступа к клиенту

    async def _initialize_client(self) -> None:
        """Инициализирует клиент для работы с Google Sheets с повторными попытками."""
        if self._client is not None:
            return

        async with self._lock:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info("Инициализация Google Sheets клиента...")
                    logger.info(f"Проверка файла credentials.json в: {__file__}")
                    credentials = Credentials.from_service_account_file(
                        'credentials.json',
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                    logger.info("Аутентификация клиента...")
                    self._client = authorize(credentials)
                    logger.info(f"Попытка открыть таблицу с ID: {SPREADSHEET_ID}")
                    self._spreadsheet = self._client.open_by_key(SPREADSHEET_ID)
                    logger.info("Таблица успешно открыта")
                    return
                except Exception as e:
                    logger.error(f"Ошибка аутентификации в Google Sheets (попытка {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
                    else:
                        raise GoogleSheetsError(f"Ошибка аутентификации в Google Sheets: {e}")

    async def get_all_properties(self) -> List[Dict[str, Any]]:
        """Получает все объекты недвижимости из листа Listings."""
        await self._initialize_client()
        try:
            sheet = self._spreadsheet.worksheet('Listings')
            records = sheet.get_all_records()
            logger.info(f"Получено {len(records)} объектов из листа Listings")
            return records
        except gspread.WorksheetNotFound:
            logger.error("Лист Listings не найден")
            raise ServiceError("Лист Listings не найден")
        except Exception as e:
            logger.error(f"Ошибка получения объектов: {e}")
            raise ServiceError("Не удалось загрузить объекты")

    async def get_property_by_id(self, property_id: int) -> Optional[Dict[str, Any]]:
        """Получает объект недвижимости по ID."""
        await self._initialize_client()
        try:
            sheet = self._spreadsheet.worksheet('Listings')
            records = sheet.get_all_records()
            for record in records:
                if record.get('id') == property_id:
                    logger.info(f"Найден объект с ID {property_id}")
                    return record
            logger.warning(f"Объект с ID {property_id} не найден")
            return None
        except gspread.WorksheetNotFound:
            logger.error("Лист Listings не найден")
            raise ServiceError("Лист Listings не найден")
        except Exception as e:
            logger.error(f"Ошибка получения объекта по ID {property_id}: {e}")
            raise ServiceError("Не удалось найти объект")

    async def get_listings(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Получает отфильтрованные объекты недвижимости."""
        await self._initialize_client()
        try:
            sheet = self._spreadsheet.worksheet('Listings')
            records = sheet.get_all_records()
            filtered = []
            for record in records:
                if all(
                    str(record.get(key)) == str(value)  # Преобразование для сравнения
                    for key, value in filters.items()
                    if key != 'max_price'
                ):
                    if 'max_price' in filters and float(record.get('price', float('inf'))) <= float(filters['max_price']):
                        filtered.append(record)
                    elif 'max_price' not in filters:
                        filtered.append(record)
            logger.info(f"Найдено {len(filtered)} объектов после фильтрации")
            return filtered
        except gspread.WorksheetNotFound:
            logger.error("Лист Listings не найден")
            raise ServiceError("Лист Listings не найден")
        except Exception as e:
            logger.error(f"Ошибка фильтрации объектов: {e}")
            raise ServiceError("Не удалось получить объекты")

    async def save_request(self, request_data: Dict[str, Any]):
        """Сохраняет заявку в лист Requests."""
        await self._initialize_client()
        try:
            sheet = self._spreadsheet.worksheet('Requests')
            values = [
                request_data['timestamp'],
                request_data['user_id'],
                request_data['username'],
                request_data['user_name'],
                request_data['phone'],
                request_data.get('property_id', 'N/A'),  # По умолчанию 'N/A'
                request_data.get('property_address', 'N/A')  # По умолчанию 'N/A'
            ]
            sheet.append_row(values)
            logger.info("Заявка успешно сохранена")
        except gspread.WorksheetNotFound:
            logger.error("Лист Requests не найден")
            raise ServiceError("Лист Requests не найден")
        except Exception as e:
            logger.error(f"Ошибка сохранения заявки: {e}")
            raise ServiceError("Не удалось сохранить заявку")

    async def close(self):
        """Закрывает клиент для освобождения ресурсов."""
        if self._client:
            self._client = None
            self._spreadsheet = None
            logger.info("Клиент Google Sheets закрыт")

# Глобальный экземпляр сервиса
google_sheets_service = GoogleSheetsService()