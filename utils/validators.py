"""
Модуль валидации данных для риэлторского бота.
Этот модуль содержит функции для проверки корректности пользовательского ввода
и данных из внешних источников, что помогает предотвратить ошибки и улучшить UX.
"""

import re
from typing import List, Optional, Union
from urllib.parse import urlparse
from config import MAX_COMMENT_LENGTH, SUPPORTED_IMAGE_FORMATS
from exceptions.custom_exceptions import ValidationError


class DataValidator:
    """
    Класс для валидации различных типов данных в боте.
    Использует статические методы для легкого использования без создания экземпляра.
    """
    
    @staticmethod
    def validate_name(name: str) -> str:
        """
        Проверяет корректность имени пользователя.
        
        Args:
            name: Строка с именем для проверки
            
        Returns:
            Очищенное и валидное имя
            
        Raises:
            ValidationError: Если имя не соответствует требованиям
        """
        if not name or not name.strip():
            raise ValidationError("Имя не может быть пустым")
        
        cleaned_name = name.strip()
        
        # Проверяем длину имени
        if len(cleaned_name) < 2:
            raise ValidationError("Имя слишком короткое (минимум 2 символа)")
        
        if len(cleaned_name) > 50:
            raise ValidationError("Имя слишком длинное (максимум 50 символов)")
        
        # Проверяем, что имя содержит только буквы, пробелы и дефисы
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-]+$', cleaned_name):
            raise ValidationError("Имя может содержать только буквы, пробелы и дефисы")
        
        return cleaned_name
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """
        Валидирует и нормализует номер телефона.
        
        Args:
            phone: Строка с номером телефона
            
        Returns:
            Нормализованный номер телефона
            
        Raises:
            ValidationError: Если номер некорректен
        """
        if not phone or not phone.strip():
            raise ValidationError("Номер телефона не может быть пустым")
        
        # Удаляем все символы кроме цифр и знака +
        cleaned_phone = re.sub(r'[^\d+]', '', phone.strip())
        
        # Проверяем базовый формат российского номера
        if cleaned_phone.startswith('+7'):
            if len(cleaned_phone) != 12:  # +7 + 10 цифр
                raise ValidationError("Некорректный формат российского номера")
        elif cleaned_phone.startswith('8'):
            if len(cleaned_phone) != 11:  # 8 + 10 цифр
                raise ValidationError("Некорректный формат российского номера")
            # Заменяем 8 на +7
            cleaned_phone = '+7' + cleaned_phone[1:]
        elif cleaned_phone.startswith('7'):
            if len(cleaned_phone) != 11:  # 7 + 10 цифр
                raise ValidationError("Некорректный формат российского номера")
            # Добавляем +
            cleaned_phone = '+' + cleaned_phone
        else:
            raise ValidationError("Номер должен начинаться с +7, 8 или 7")
        
        return cleaned_phone
    
    @staticmethod
    def validate_comment(comment: str) -> str:
        """
        Проверяет корректность комментария пользователя.
        Комментарий может быть пустым, но не должен превышать максимальную длину.
        
        Args:
            comment: Строка с комментарием
            
        Returns:
            Очищенный комментарий или стандартное значение
        """
        if not comment or not comment.strip():
            return "Без комментариев"
        
        cleaned_comment = comment.strip()
        
        if len(cleaned_comment) > MAX_COMMENT_LENGTH:
            raise ValidationError(
                f"Комментарий слишком длинный (максимум {MAX_COMMENT_LENGTH} символов)", 
                "comment", 
                comment
            )
        
        return cleaned_comment
    
    @staticmethod
    def validate_photo_urls(photo_urls: Union[str, List[str]]) -> List[str]:
        """
        Валидирует список URL'ов фотографий объектов недвижимости.
        Проверяет корректность URL'ов и поддерживаемые форматы изображений.
        
        Args:
            photo_urls: Строка с URL'ами через запятую или список URL'ов
            
        Returns:
            Список валидных URL'ов
        """
        if not photo_urls:
            return []
        
        # Приводим к списку, если получили строку
        if isinstance(photo_urls, str):
            urls_list = [url.strip() for url in photo_urls.split(',') if url.strip()]
        else:
            urls_list = photo_urls
        
        valid_urls = []
        
        for url in urls_list:
            if DataValidator._is_valid_image_url(url):
                valid_urls.append(url)
        
        return valid_urls
    
    @staticmethod
    def _is_valid_image_url(url: str) -> bool:
        """
        Проверяет, является ли URL корректной ссылкой на изображение.
        
        Args:
            url: URL для проверки
            
        Returns:
            True, если URL корректен и ведет на изображение
        """
        if not url or not url.strip():
            return False
        
        # Базовая проверка URL
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False
        except Exception:
            return False
        
        # Проверяем, что URL начинается с http/https
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Проверяем расширение файла (упрощенная проверка)
        url_lower = url.lower()
        
        # Учитываем, что современные CDN могут не иметь расширения в URL
        # но для базовой валидации проверим наличие одного из поддерживаемых форматов
        has_supported_format = any(format_ext in url_lower for format_ext in SUPPORTED_IMAGE_FORMATS)
        
        # Также принимаем URL'ы популярных сервисов изображений
        popular_image_hosts = [
            'imgur.com', 'drive.google.com', 'dropbox.com', 
            'yandex.ru', 'ya.ru', 'vk.com', 'telegram.org'
        ]
        
        has_popular_host = any(host in url_lower for host in popular_image_hosts)
        
        return has_supported_format or has_popular_host
    
    @staticmethod
    def validate_listing_data(listing_dict: dict) -> dict:
        """
        Валидирует данные объекта недвижимости из внешнего источника.
        Проверяет наличие обязательных полей и их корректность.
        
        Args:
            listing_dict: Словарь с данными объекта
            
        Returns:
            Словарь с валидными и нормализованными данными
            
        Raises:
            ValidationError: Если данные некорректны
        """
        if not isinstance(listing_dict, dict):
            raise ValidationError("Данные объекта должны быть в формате словаря")
        
        # Список обязательных полей для объекта недвижимости
        required_fields = ['id', 'property_type', 'deal_type', 'district', 'price']
        
        for field in required_fields:
            if field not in listing_dict or not listing_dict[field]:
                raise ValidationError(f"Отсутствует обязательное поле: {field}")
        
        # Нормализуем данные
        validated_listing = {
            'id': str(listing_dict['id']),  # Приводим ID к строке для единообразия
            'property_type': str(listing_dict['property_type']).strip(),
            'deal_type': str(listing_dict['deal_type']).strip(),
            'district': str(listing_dict['district']).strip(),
            'price': DataValidator._validate_price(listing_dict['price']),
            'rooms': str(listing_dict.get('rooms', '')).strip(),
            'description': str(listing_dict.get('description', 'Описание не указано')).strip(),
            'photo_url': DataValidator.validate_photo_urls(listing_dict.get('photo_url', []))
        }
        
        return validated_listing
    
    @staticmethod
    def _validate_price(price: Union[str, int, float]) -> float:
        """
        Валидирует и нормализует цену объекта недвижимости.
        
        Args:
            price: Цена в любом формате
            
        Returns:
            Нормализованная цена как float
            
        Raises:
            ValidationError: Если цену невозможно обработать
        """
        if not price and price != 0:
            raise ValidationError("Цена не может быть пустой")
        
        try:
            # Если цена строка, пытаемся извлечь числовое значение
            if isinstance(price, str):
                # Удаляем все символы кроме цифр и точки
                price_clean = re.sub(r'[^\d.]', '', price)
                if not price_clean:
                    raise ValidationError("Не удается извлечь цену из строки")
                price_float = float(price_clean)
            else:
                price_float = float(price)
            
            if price_float < 0:
                raise ValidationError("Цена не может быть отрицательной")
            
            if price_float > 1_000_000_000:  # Ограничение в 1 миллиард
                raise ValidationError("Цена слишком большая")
            
            return price_float
            
        except (ValueError, TypeError):
            raise ValidationError(f"Некорректный формат цены: {price}")


# Функции для обратной совместимости (если они используются в других местах)
def validate_phone(phone: str) -> str:
    """Функция-обертка для метода класса DataValidator."""
    return DataValidator.validate_phone(phone)


def validate_name(name: str) -> str:
    """Функция-обертка для метода класса DataValidator."""
    return DataValidator.validate_name(name)