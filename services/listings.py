"""
Сервис для работы с объектами недвижимости.
Этот модуль содержит логику навигации по объектам, обработки фотографий
и формирования сообщений для пользователей. Устраняет дублирование кода
между модулями search и request.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from services.sheets import google_sheets_service
from utils.keyboards import get_listing_menu, get_main_menu
from utils.validators import DataValidator
from exceptions.custom_exceptions import ListingNotFoundError, PhotoProcessingError
from config import ADMIN_ID

logger = logging.getLogger(__name__)

class ListingService:
    """
    Сервис для работы с объектами недвижимости.
    Предоставляет методы для навигации, отображения и взаимодействия с объектами.
    """
    
    @staticmethod
    async def get_filtered_listings(search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Получает отфильтрованные объекты недвижимости на основе критериев поиска.
        
        Args:
            search_criteria: Словарь с критериями поиска
            
        Returns:
            Список подходящих объектов недвижимости
        """
        logger.info(f"Поиск объектов с критериями: {search_criteria}")
        
        filters = ListingService._convert_search_criteria_to_filters(search_criteria)
        
        listings = await google_sheets_service.get_listings(filters)
        
        logger.info(f"Найдено {len(listings)} объектов по критериям")
        return listings
    
    @staticmethod
    def _convert_search_criteria_to_filters(criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует критерии поиска пользователя в фильтры для сервиса Google Sheets.
        
        Args:
            criteria: Критерии поиска от пользователя
            
        Returns:
            Словарь фильтров для Google Sheets сервиса
        """
        filters = {}
        
        if 'property_type' in criteria:
            property_type = criteria['property_type'].replace('property_type_', '') if criteria['property_type'].startswith('property_type_') else criteria['property_type']
            filters['property_type'] = property_type
        
        if 'deal_type' in criteria:
            deal_type = criteria['deal_type'].replace('deal_type_', '') if criteria['deal_type'].startswith('deal_type_') else criteria['deal_type']
            filters['deal_type'] = deal_type
        
        if 'district' in criteria:
            district = criteria['district'].replace('district_', '') if criteria['district'].startswith('district_') else criteria['district']
            filters['district'] = district
        
        if 'rooms' in criteria and criteria['rooms']:
            filters['rooms'] = criteria['rooms']
        
        if 'budget' in criteria:
            budget_str = criteria['budget'].replace('budget_', '') if criteria['budget'].startswith('budget_') else criteria['budget']
            try:
                if '-' in budget_str:
                    max_price = budget_str.split('-')[-1]
                else:
                    max_price = budget_str
                filters['max_price'] = float(max_price)
            except (ValueError, IndexError):
                logger.warning(f"Не удалось обработать бюджет: {budget_str}")
        
        return filters
    
    @staticmethod
    async def show_listing(
        message: Message, 
        state: FSMContext, 
        listing_index: int = 0,
        photo_index: int = 0,
        comments_provided: bool = False
    ) -> None:
        """
        Отображает объект недвижимости пользователю с навигацией.
        
        Args:
            message: Объект сообщения для ответа
            state: Контекст состояния FSM
            listing_index: Индекс текущего объекта
            photo_index: Индекс текущей фотографии
            comments_provided: Были ли предоставлены комментарии
        """
        data = await state.get_data()
        filtered_listings = data.get('filtered_listings', [])
        
        if not filtered_listings:
            await message.answer(
                "Объекты не найдены по заданным критериям.",
                reply_markup=get_main_menu()
            )
            return
        
        if listing_index >= len(filtered_listings):
            logger.error(f"Индекс объекта {listing_index} превышает количество объектов {len(filtered_listings)}")
            listing_index = 0
        
        listing = filtered_listings[listing_index]
        photo_urls = DataValidator.validate_photo_urls(listing.get('photo_url', []))
        
        message_text = ListingService._format_listing_message(
            listing, listing_index + 1, len(filtered_listings)
        )
        
        keyboard = get_listing_menu(
            listing_exists=True,
            comments_provided=comments_provided,
            has_next_listing=listing_index < len(filtered_listings) - 1,
            listing_index=listing_index,
            photo_index=photo_index,
            total_photos=len(photo_urls),
            total_listings=len(filtered_listings),
            listing_id=listing['id']
        )
        
        await message.answer(message_text, reply_markup=keyboard)
        
        if photo_urls and photo_index < len(photo_urls):
            try:
                await message.answer_photo(photo=photo_urls[photo_index])
                logger.info(f"Отправлена фотография {photo_index + 1}/{len(photo_urls)} для объекта {listing['id']}")
            except Exception as e:
                logger.error(f"Ошибка при отправке фотографии {photo_urls[photo_index]}: {e}")
                await message.answer("⚠️ Не удалось загрузить фотографию объекта")
    
    @staticmethod
    def _format_listing_message(listing: Dict[str, Any], current_num: int, total_num: int) -> str:
        """
        Форматирует сообщение с информацией об объекте недвижимости.
        
        Args:
            listing: Данные объекта
            current_num: Номер текущего объекта
            total_num: Общее количество объектов
            
        Returns:
            Отформатированное сообщение
        """
        price_formatted = f"{listing['price']:,.0f}".replace(',', ' ')
        
        message = f"🏠 Объект {current_num}/{total_num}\n"
        message += f"🆔 ID: {listing['id']}\n"
        message += f"🏢 Тип: {listing['property_type']}\n"
        message += f"💼 Сделка: {listing['deal_type']}\n"
        message += f"📍 Район: {listing['district']}\n"
        message += f"💰 Цена: {price_formatted} ₽\n"
        
        if listing.get('rooms') and str(listing['rooms']).strip():
            message += f"🛏 Комнат: {listing['rooms']}\n"
        
        message += f"\n📝 {listing.get('description', 'Описание не указано')}"
        
        return message
    
    @staticmethod
    def get_property_photos(listing: Dict[str, Any]) -> List[str]:
        """
        Получает список URL фотографий для объекта недвижимости.
        
        Args:
            listing: Словарь с информацией об объекте
        
        Returns:
            List[str]: Список URL фотографий
        """
        try:
            photos = listing.get('photo_url', [])
            if isinstance(photos, str):
                photos = photos.split(',') if photos else []
            return [photo.strip() for photo in photos if photo.strip()]
        except Exception as e:
            logger.error(f"Ошибка получения фотографий объекта: {e}")
            return []
    
    @staticmethod
    async def handle_photo_navigation(
        callback: CallbackQuery, 
        state: FSMContext, 
        direction: str,
        target_listing_index: int,
        target_photo_index: int
    ) -> None:
        """
        Обрабатывает навигацию по фотографиям объекта.
        
        Args:
            callback: Объект callback запроса
            state: Контекст состояния FSM
            direction: Направление навигации ('next' или 'prev')
            target_listing_index: Целевой индекс объекта
            target_photo_index: Целевой индекс фотографии
        """
        data = await state.get_data()
        filtered_listings = data.get('filtered_listings', [])
        
        if not filtered_listings or target_listing_index >= len(filtered_listings):
            await callback.answer("Объект не найден.")
            return
        
        listing = filtered_listings[target_listing_index]
        photo_urls = DataValidator.validate_photo_urls(listing.get('photo_url', []))
        
        if not photo_urls:
            await callback.answer("У объекта нет фотографий.")
            return
        
        if target_photo_index < 0:
            await callback.answer("Это первое фото.")
            return
        
        if target_photo_index >= len(photo_urls):
            await callback.answer("Больше нет фотографий.")
            return
        
        await state.update_data(
            current_listing_index=target_listing_index,
            current_photo_index=target_photo_index
        )
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        caption = ListingService._format_photo_caption(
            listing, target_listing_index + 1, len(filtered_listings),
            target_photo_index + 1, len(photo_urls)
        )
        
        keyboard = get_listing_menu(
            listing_exists=True,
            comments_provided=bool(data.get('comments')),
            has_next_listing=target_listing_index < len(filtered_listings) - 1,
            listing_index=target_listing_index,
            photo_index=target_photo_index,
            total_photos=len(photo_urls),
            total_listings=len(filtered_listings),
            listing_id=listing['id']
        )
        
        try:
            await callback.message.answer_photo(
                photo=photo_urls[target_photo_index],
                caption=caption,
                reply_markup=keyboard
            )
            logger.info(f"Показано фото {target_photo_index + 1}/{len(photo_urls)} объекта {listing['id']}")
        except Exception as e:
            logger.error(f"Ошибка при отправке фотографии: {e}")
            raise PhotoProcessingError(f"Не удалось загрузить фотографию", photo_urls[target_photo_index])
        
        await callback.answer()
    
    @staticmethod
    def _format_photo_caption(
        listing: Dict[str, Any], 
        listing_num: int, 
        total_listings: int,
        photo_num: int, 
        total_photos: int
    ) -> str:
        """
        Форматирует подпись для фотографии объекта.
        
        Args:
            listing: Данные объекта
            listing_num: Номер объекта
            total_listings: Общее количество объектов
            photo_num: Номер фотографии
            total_photos: Общее количество фотографий
            
        Returns:
            Отформатированная подпись
        """
        price_formatted = f"{listing['price']:,.0f}".replace(',', ' ')
        
        caption = f"🏠 Объект {listing_num}/{total_listings} | 📸 Фото {photo_num}/{total_photos}\n"
        caption += f"🆔 ID: {listing['id']}\n"
        caption += f"💰 Цена: {price_formatted} ₽\n"
        caption += f"📍 {listing['district']}\n\n"
        caption += f"📝 {listing.get('description', 'Описание не указано')}"
        
        return caption
    
    @staticmethod
    async def handle_listing_navigation(
        callback: CallbackQuery,
        state: FSMContext,
        target_listing_index: int
    ) -> None:
        """
        Обрабатывает навигацию между объектами недвижимости.
        
        Args:
            callback: Объект callback запроса
            state: Контекст состояния FSM
            target_listing_index: Индекс целевого объекта
        """
        data = await state.get_data()
        filtered_listings = data.get('filtered_listings', [])
        
        if not filtered_listings:
            await callback.answer("Нет доступных объектов.")
            return
        
        if target_listing_index < 0:
            await callback.answer("Это первый объект.")
            return
        
        if target_listing_index >= len(filtered_listings):
            await callback.answer("Больше нет объектов.")
            return
        
        await state.update_data(
            current_listing_index=target_listing_index,
            current_photo_index=0
        )
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        await ListingService.show_listing(
            callback.message, 
            state, 
            target_listing_index, 
            0,
            bool(data.get('comments'))
        )
        
        await callback.answer()
    
    @staticmethod
    async def handle_interest(
        callback: CallbackQuery,
        state: FSMContext,
        listing_id: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Обрабатывает выражение интереса пользователя к объекту.
        """
        from handlers.admin import log_user_action
        
        data = await state.get_data()
        filtered_listings = data.get('filtered_listings', [])
        
        listing = next((l for l in filtered_listings if str(l['id']) == str(listing_id)), None)
        
        if not listing:
            await callback.answer("Объект не найден.")
            return False, None
        
        log_user_action(callback.from_user.id, callback.from_user.username, f"Показано интерес к объекту ID: {listing_id}")
        
        if ADMIN_ID:
            try:
                admin_message = (
                    f"🔥 Новый интерес к объекту!\n\n"
                    f"👤 Пользователь: {callback.from_user.id} (@{callback.from_user.username or 'no_username'})\n"
                    f"🆔 Объект ID: {listing_id}\n"
                    f"🏠 Тип: {listing['property_type']}\n"
                    f"📍 Район: {listing['district']}\n"
                    f"💰 Цена: {listing['price']:,.0f} ₽\n\n"
                    f"📝 Описание:\n{listing.get('description', 'Описание не указано')}"
                )
                
                for admin_id in ADMIN_ID:
                    await callback.bot.send_message(admin_id, admin_message)
                logger.info(f"Уведомление об интересе к объекту {listing_id} отправлено админу")
                
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления админу: {e}")
        
        await callback.answer("Ваш интерес зафиксирован!")
        logger.info(f"Пользователь {callback.from_user.id} заинтересован в объекте {listing_id}")
        
        return True, listing