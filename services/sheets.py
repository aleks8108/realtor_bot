"""
Единый сервис для работы с Google Sheets.
Этот модуль содержит всю логику взаимодействия с Google Sheets API,
включая получение объектов недвижимости и сохранение заявок пользователей.
"""

import gspread
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from oauth2client.service_account import ServiceAccountCredentials

from config import (
    GOOGLE_SHEETS_SCOPE, GOOGLE_SHEETS_CREDENTIALS, SPREADSHEET_ID,
    LISTINGS_SHEET_NAME, REQUESTS_SHEET_NAME, MAX_RETRIES, RETRY_DELAY
)
from exceptions.custom_exceptions import GoogleSheetsError, ValidationError
from utils.validators import DataValidator
from services.error_handler import retry_operation

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """
    Сервис для работы с Google Sheets.
    Предоставляет методы для чтения объектов недвижимости и сохранения заявок.
    """
    
    def __init__(self):
        """Инициализация сервиса с аутентификацией в Google Sheets."""
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """
        Инициализирует клиент Google Sheets с аутентификацией.
        Использует служебные учетные данные из файла credentials.json.
        """
        try:
            logger.info("Инициализация клиента Google Sheets...")
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                str(GOOGLE_SHEETS_CREDENTIALS), 
                GOOGLE_SHEETS_SCOPE
            )
            self._client = gspread.authorize(creds)
            self._spreadsheet = self._client.open_by_key(SPREADSHEET_ID)
            logger.info("✓ Клиент Google Sheets успешно инициализирован")
        except FileNotFoundError:
            raise GoogleSheetsError(
                f"Файл credentials.json не найден по пути {GOOGLE_SHEETS_CREDENTIALS}",
                "authenticate"
            )
        except Exception as e:
            raise GoogleSheetsError(
                f"Ошибка аутентификации в Google Sheets: {str(e)}",
                "authenticate"
            )
    
    async def get_listings(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Получает список объектов недвижимости из Google Sheets.
        
        Args:
            filters: Словарь фильтров для отбора объектов (опционально)
            
        Returns:
            Список словарей с данными объектов недвижимости
            
        Raises:
            GoogleSheetsError: При ошибках работы с Google Sheets API
        """
        async def _fetch_listings():
            try:
                logger.info("Получение данных объектов недвижимости...")
                worksheet = self._spreadsheet.worksheet(LISTINGS_SHEET_NAME)
                raw_data = worksheet.get_all_records()
                
                logger.info(f"Получено {len(raw_data)} записей из таблицы")
                
                # Валидируем и нормализуем данные
                validated_listings = []
                for i, listing_data in enumerate(raw_data, 1):
                    try:
                        # Пропускаем пустые строки
                        if not any(str(value).strip() for value in listing_data.values()):
                            continue
                            
                        validated_listing = DataValidator.validate_listing_data(listing_data)
                        validated_listings.append(validated_listing)
                        
                    except ValidationError as e:
                        logger.warning(f"Строка {i} пропущена из-за ошибки валидации: {e.message}")
                        continue
                
                logger.info(f"Валидировано {len(validated_listings)} объектов недвижимости")
                
                # Применяем фильтры, если они переданы
                if filters:
                    validated_listings = self._apply_filters(validated_listings, filters)
                    logger.info(f"После фильтрации осталось {len(validated_listings)} объектов")
                
                return validated_listings
                
            except gspread.WorksheetNotFound:
                raise GoogleSheetsError(
                    f"Лист '{LISTINGS_SHEET_NAME}' не найден в таблице",
                    "read",
                    LISTINGS_SHEET_NAME
                )
            except gspread.APIError as e:
                raise GoogleSheetsError(
                    f"Ошибка Google Sheets API при чтении данных: {str(e)}",
                    "read",
                    LISTINGS_SHEET_NAME
                )
            except Exception as e:
                raise GoogleSheetsError(
                    f"Непредвиденная ошибка при получении объектов: {str(e)}",
                    "read",
                    LISTINGS_SHEET_NAME
                )
        
        return await retry_operation(
            _fetch_listings,
            max_retries=MAX_RETRIES,
            delay=RETRY_DELAY
        )
    
    def _apply_filters(self, listings: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Применяет фильтры к списку объектов недвижимости.
        
        Args:
            listings: Список объектов для фильтрации
            filters: Словарь с критериями фильтрации
            
        Returns:
            Отфильтрованный список объектов
        """
        filtered_listings = listings.copy()
        
        # Фильтр по типу недвижимости
        if 'property_type' in filters and filters['property_type']:
            filtered_listings = [
                listing for listing in filtered_listings
                if listing['property_type'].lower() == filters['property_type'].lower()
            ]
        
        # Фильтр по типу сделки
        if 'deal_type' in filters and filters['deal_type']:
            filtered_listings = [
                listing for listing in filtered_listings
                if listing['deal_type'].lower() == filters['deal_type'].lower()
            ]
        
        # Фильтр по району
        if 'district' in filters and filters['district']:
            filtered_listings = [
                listing for listing in filtered_listings
                if listing['district'].lower() == filters['district'].lower()
            ]
        
        # Фильтр по количеству комнат
        if 'rooms' in filters and filters['rooms'] and filters['rooms'] != 'none':
            filtered_listings = [
                listing for listing in filtered_listings
                if str(listing['rooms']).strip() == str(filters['rooms']).strip()
            ]
        
        # Фильтр по максимальной цене
        if 'max_price' in filters and filters['max_price']:
            try:
                max_price = float(filters['max_price'])
                filtered_listings = [
                    listing for listing in filtered_listings
                    if listing['price'] <= max_price
                ]
            except (ValueError, TypeError):
                logger.warning(f"Некорректное значение max_price: {filters['max_price']}")
        
        # Фильтр по минимальной цене
        if 'min_price' in filters and filters['min_price']:
            try:
                min_price = float(filters['min_price'])
                filtered_listings = [
                    listing for listing in filtered_listings
                    if listing['price'] >= min_price
                ]
            except (ValueError, TypeError):
                logger.warning(f"Некорректное значение min_price: {filters['min_price']}")
        
        return filtered_listings
    
    async def save_request(self, request_data: Dict[str, Any]) -> None:
        """
        Сохраняет заявку пользователя в Google Sheets.
        
        Args:
            request_data: Словарь с данными заявки пользователя
            
        Raises:
            GoogleSheetsError: При ошибках работы с Google Sheets API
            ValidationError: При некорректных данных в заявке
        """
        async def _save_request():
            try:
                logger.info(f"Сохранение заявки от пользователя {request_data.get('user_id')}")
                
                # Валидируем обязательные поля заявки
                required_fields = ['name', 'phone', 'property_type', 'deal_type', 'district', 'budget']
                missing_fields = [field for field in required_fields if not request_data.get(field)]
                
                if missing_fields:
                    raise ValidationError(f"Отсутствуют обязательные поля в заявке: {', '.join(missing_fields)}")
                
                # Валидируем данные
                validated_data = {
                    'name': DataValidator.validate_name(request_data['name']),
                    'phone': DataValidator.validate_phone(request_data['phone']),
                    'property_type': str(request_data['property_type']).strip(),
                    'deal_type': str(request_data['deal_type']).strip(),
                    'district': str(request_data['district']).strip(),
                    'budget': str(request_data['budget']).strip(),
                    'rooms': str(request_data.get('rooms', '')).strip(),
                    'comments': DataValidator.validate_comment(request_data.get('comments', '')),
                    'user_id': str(request_data.get('user_id', '')),
                    'username': str(request_data.get('username', 'no_username')),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Получаем worksheet для заявок
                worksheet = self._spreadsheet.worksheet(REQUESTS_SHEET_NAME)
                
                # Проверяем наличие заголовков
                headers = worksheet.row_values(1)
                expected_headers = list(validated_data.keys())
                
                if not headers:
                    # Если заголовков нет, добавляем их
                    logger.info("Добавление заголовков в лист заявок")
                    worksheet.insert_row(expected_headers, 1)
                    headers = expected_headers
                
                # Формируем строку для записи в том же порядке, что и заголовки
                row_data = [validated_data.get(header, '') for header in headers]
                
                # Добавляем строку
                worksheet.append_row(row_data)
                
                logger.info(f"✓ Заявка успешно сохранена для пользователя {validated_data['user_id']}")
                
            except gspread.WorksheetNotFound:
                raise GoogleSheetsError(
                    f"Лист '{REQUESTS_SHEET_NAME}' не найден в таблице",
                    "write",
                    REQUESTS_SHEET_NAME
                )
            except gspread.APIError as e:
                raise GoogleSheetsError(
                    f"Ошибка Google Sheets API при сохранении заявки: {str(e)}",
                    "write",
                    REQUESTS_SHEET_NAME
                )
            except ValidationError:
                raise  # Пробрасываем ValidationError дальше
            except Exception as e:
                raise GoogleSheetsError(
                    f"Непредвиденная ошибка при сохранении заявки: {str(e)}",
                    "write",
                    REQUESTS_SHEET_NAME
                )
        
        await retry_operation(
            _save_request,
            max_retries=MAX_RETRIES,
            delay=RETRY_DELAY
        )
    
    async def get_listing_by_id(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает конкретный объект недвижимости по его ID.
        
        Args:
            listing_id: ID объекта для поиска
            
        Returns:
            Словарь с данными объекта или None, если не найден
        """
        listings = await self.get_listings()
        return next((listing for listing in listings if str(listing['id']) == str(listing_id)), None)
    
    async def get_requests_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получает историю заявок для административной панели.
        
        Args:
            limit: Максимальное количество заявок для получения
            
        Returns:
            Список словарей с данными заявок
        """
        async def _fetch_requests():
            try:
                worksheet = self._spreadsheet.worksheet(REQUESTS_SHEET_NAME)
                data = worksheet.get_all_records()
                
                # Сортируем по timestamp (новые первые) и ограничиваем количество
                sorted_data = sorted(data, key=lambda x: x.get('timestamp', ''), reverse=True)
                return sorted_data[:limit]
                
            except gspread.WorksheetNotFound:
                logger.warning(f"Лист '{REQUESTS_SHEET_NAME}' не найден")
                return []
            except Exception as e:
                raise GoogleSheetsError(
                    f"Ошибка при получении истории заявок: {str(e)}",
                    "read",
                    REQUESTS_SHEET_NAME
                )
        
        return await retry_operation(_fetch_requests, max_retries=2, delay=1.0)


# Создаем единый экземпляр сервиса для использования во всем приложении
google_sheets_service = GoogleSheetsService()