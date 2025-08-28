"""
Модуль для работы с Google Sheets API.
Предоставляет асинхронные методы для взаимодействия с таблицами,
включая получение объектов недвижимости, фильтрацию и сохранение заявок.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from google.oauth2.service_account import Credentials
import gspread
from gspread import authorize, Spreadsheet
from gspread.exceptions import WorksheetNotFound
import asyncio
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from googleapiclient.errors import HttpError
from requests.exceptions import SSLError, RequestException, ConnectionError
from exceptions.custom_exceptions import GoogleSheetsError, ServiceError

logger = logging.getLogger(__name__)

SPREADSHEET_ID = '1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w'

def with_retry(max_retries=5, backoff_factor=1):
    """Декоратор для повторных попыток с экспоненциальной задержкой и обработкой SSL."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (SSLError, ConnectionError, RequestException, HttpError) as e:
                    logger.error(f"Ошибка в {func.__name__} (попытка {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise
                except Exception as e:
                    logger.error(f"Неожиданная ошибка в {func.__name__} (попытка {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise
        return wrapper
    return decorator

class GoogleSheetsService:
    def __init__(self):
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[Spreadsheet] = None
        self._lock = asyncio.Lock()
        # Настройка HTTP-адаптера с повторными попытками и таймаутом
        self._session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504, 429],
            allowed_methods=["GET", "POST"],
            raise_on_redirect=True,
            raise_on_status=True
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("https://", adapter)
        # Устанавливаем глобальный таймаут для сессии
        self._session.timeout = 30  # Таймаут 30 секунд

    @with_retry()
    async def _initialize_client(self) -> None:
        """Инициализирует клиент для работы с Google Sheets с повторными попытками."""
        if self._client is not None:
            return

        async with self._lock:
            try:
                logger.info("Инициализация Google Sheets клиента...")
                logger.info(f"Проверка файла credentials.json в: {__file__}")
                credentials = Credentials.from_service_account_file(
                    'credentials.json',
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                logger.info("Проверка учетных данных...")
                import google.auth.transport.requests
                request = google.auth.transport.requests.Request(session=self._session)
                credentials.refresh(request)
                logger.info("Аутентификация клиента...")
                self._client = authorize(credentials)
                logger.info(f"Попытка открыть таблицу с ID: {SPREADSHEET_ID}")
                self._spreadsheet = self._client.open_by_key(SPREADSHEET_ID)
                logger.info("Таблица успешно открыта")
            except Exception as e:
                logger.error(f"Ошибка аутентификации в Google Sheets: {e}")
                raise GoogleSheetsError(f"Ошибка аутентификации в Google Sheets: {e}")

    @with_retry()
    async def get_sheet(self, sheet_name: str) -> Optional[gspread.Worksheet]:
        """Получает лист по имени с обработкой ошибок."""
        await self._initialize_client()
        try:
            return self._spreadsheet.worksheet(sheet_name)
        except WorksheetNotFound:
            logger.error(f"Лист {sheet_name} не найден")
            raise ServiceError(f"Лист {sheet_name} не найден")
        except Exception as e:
            logger.error(f"Ошибка получения листа {sheet_name}: {e}")
            raise ServiceError(f"Не удалось получить лист {sheet_name}")

    @with_retry()
    async def get_all_properties(self) -> List[Dict[str, Any]]:
        """Получает все объекты недвижимости из листа Listings."""
        await self._initialize_client()
        try:
            sheet = await self.get_sheet('Listings')
            records = sheet.get_all_records()
            logger.info(f"Получено {len(records)} объектов из листа Listings")
            return records
        except ServiceError as e:
            raise e
        except Exception as e:
            logger.error(f"Ошибка получения объектов: {e}")
            raise ServiceError("Не удалось загрузить объекты")

    @with_retry()
    async def get_property_by_id(self, property_id: int) -> Optional[Dict[str, Any]]:
        """Получает объект недвижимости по ID."""
        await self._initialize_client()
        try:
            sheet = await self.get_sheet('Listings')
            records = sheet.get_all_records()
            for record in records:
                if str(record.get('id')) == str(property_id):  # Сравнение как строк для надежности
                    logger.info(f"Найден объект с ID {property_id}")
                    return record
            logger.warning(f"Объект с ID {property_id} не найден")
            return None
        except ServiceError as e:
            raise e
        except Exception as e:
            logger.error(f"Ошибка получения объекта по ID {property_id}: {e}")
            raise ServiceError("Не удалось найти объект")

    @with_retry()
    async def get_filtered_listings(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Получает отфильтрованные объекты недвижимости на основе критериев."""
        await self._initialize_client()
        try:
            sheet = await self.get_sheet('Listings')
            all_values = sheet.get_all_values()
            if not all_values or not all_values[0]:
                raise ValueError("Лист Listings пуст или не содержит заголовков")
            headers = [header.strip() for header in all_values[0]]
            records = [dict(zip(headers, row)) for row in all_values[1:] if row]
            filtered = []
            for record in records:
                normalized_record = {
                    'id': record.get('id', ''),
                    'property_type': record.get('property_type', '').strip(),
                    'deal_type': record.get('deal_type', '').strip(),
                    'district': record.get('district', '').strip(),
                    'price': float(record.get('price', float('inf'))) if record.get('price', '').strip() else float('inf'),
                    'rooms': record.get('rooms', '').strip(),
                    'address': record.get('address', '').strip() or 'Адрес не указан',
                    'description': record.get('description', 'Описание не указано'),
                    'photo_urls': record.get('photo_urls', '').split(',') if record.get('photo_urls') else [],
                    'floor': record.get('floor', 'Не указан'),
                    'area': record.get('area', 'Не указана'),
                    'contact_info': record.get('contact_info', 'Не указаны')
                }
                matches = all(
                    str(normalized_record.get(key, '')).lower() == str(value).lower() if key != 'budget' else True
                    for key, value in criteria.items()
                    if key != 'budget' and value is not None
                )
                if matches:
                    price = float(normalized_record.get('price', float('inf')))
                    budget = float(criteria.get('budget', float('inf')))
                    if price <= budget:
                        filtered.append(normalized_record)
            logger.info(f"Найдено {len(filtered)} объектов после фильтрации")
            return filtered
        except ServiceError as e:
            raise e
        except Exception as e:
            logger.error(f"Ошибка фильтрации объектов: {e}")
            raise ServiceError("Не удалось получить объекты")

    @with_retry()
    async def get_all_requests(self) -> List[Dict[str, Any]]:
        """Получает все заявки из листа Requests."""
        await self._initialize_client()
        try:
            sheet = await self.get_sheet('Requests')
            records = sheet.get_all_records()
            logger.info(f"Получено {len(records)} заявок из листа Requests")
            return records
        except ServiceError as e:
            raise e
        except Exception as e:
            logger.error(f"Ошибка получения заявок: {e}")
            raise ServiceError("Не удалось загрузить заявки")

    @with_retry()
    async def save_request(self, request_data: Dict[str, Any]):
        """Сохраняет заявку в лист Requests."""
        await self._initialize_client()
        try:
            sheet = await self.get_sheet('Requests')
            headers = ['timestamp', 'user_id', 'username', 'user_name', 'phone', 'property_id', 'property_address', 'comments', 'status']
            existing_data = sheet.get_all_values()
            if not existing_data or existing_data[0] != headers:
                sheet.append_row(headers)
            sheet.append_row([
                request_data.get('timestamp', ''),
                str(request_data.get('user_id', '')),
                request_data.get('username', ''),
                request_data.get('user_name', ''),
                request_data.get('phone', ''),
                request_data.get('property_id', ''),
                request_data.get('property_address', ''),
                request_data.get('comments', ''),
                request_data.get('status', '')  # Добавляем значение status
            ])
            logger.info("Заявка успешно сохранена")
        except (HttpError, SSLError, RequestException) as e:
            raise ServiceError(f"Ошибка сохранения заявки: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка сохранения заявки: {e}")
            raise ServiceError(f"Не удалось сохранить заявку: {str(e)}")

    @with_retry()
    async def get_price_per_m2(self, district: str, property_type: str) -> float:
        """Получает цену за кв.м по району и типу недвижимости из листа Prices."""
        await self._initialize_client()
        try:
            sheet = await self.get_sheet('Prices')
            records = sheet.get_all_records()
            district = district.strip()
            property_type = property_type.strip()
            logger.debug(f"Ищем цену для district={district}, property_type={property_type}")
            
            property_type_mappings = {
                'Квартира': ['Квартира', 'apartment'],
                'Дом': ['Дом', 'house'],
                'Коммерческая': ['Коммерческая', 'commercial'],
                'Земельный участок': ['Земельный участок', 'land']
            }
            
            for record in records:
                record_district = record.get('district', '').strip()
                record_type = record.get('property_type', '').strip()
                if (record_district.lower() == district.lower() and
                    any(pt.lower() == record_type.lower() for pt in property_type_mappings.get(property_type, [property_type]))):
                    price = float(record.get('price_per_m2', 0))
                    logger.info(f"Найдена цена за кв.м для {district}/{property_type}: {price}")
                    return price
            logger.warning(f"Цена за кв.м для {district}/{property_type} не найдена")
            return 0.0
        except ServiceError as e:
            raise e
        except Exception as e:
            logger.error(f"Ошибка получения цены за кв.м: {e}")
            raise ServiceError("Не удалось получить цену за кв.м")

    async def close(self):
        """Закрывает клиент для освобождения ресурсов."""
        if self._client:
            self._client = None
            self._spreadsheet = None
            logger.info("Клиент Google Sheets закрыт")

# Глобальный экземпляр сервиса
google_sheets_service = GoogleSheetsService()