"""
Модуль клавиатур для риэлторского бота.
Содержит функции для создания inline и reply клавиатур для различных сценариев.
"""

import logging
from typing import Optional, List, Dict, Any
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardMarkup, KeyboardButton
)

logger = logging.getLogger(__name__)


def get_main_menu() -> InlineKeyboardMarkup:
    """
    Создает основное меню бота с главными функциями.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура главного меню
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="request")],
        [InlineKeyboardButton(text="🔍 Поиск недвижимости", callback_data="search")],
        [InlineKeyboardButton(text="📞 Связаться с риэлтором", callback_data="contact")]
    ])


def get_start_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает reply-клавиатуру для начального взаимодействия.
    Полезна для пользователей, которые предпочитают обычные кнопки.
    
    Returns:
        ReplyKeyboardMarkup: Reply-клавиатура с основными функциями
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Оставить заявку")],
            [KeyboardButton(text="🔍 Поиск недвижимости")],
            [KeyboardButton(text="📞 Связаться с риэлтором")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_property_type_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора типа недвижимости.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с типами недвижимости
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏠 Квартира", callback_data="property_type_Квартира"),
            InlineKeyboardButton(text="🏘 Дом", callback_data="property_type_Дом")
        ],
        [
            InlineKeyboardButton(text="🏢 Коммерческая", callback_data="property_type_Коммерческая"),
            InlineKeyboardButton(text="🌱 Участок", callback_data="property_type_Земельный участок")
        ],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="return_to_menu")]
    ])


def get_deal_type_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора типа сделки.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с типами сделок
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Покупка", callback_data="deal_type_Покупка"),
            InlineKeyboardButton(text="🏠 Аренда", callback_data="deal_type_Аренда")
        ],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="return_to_menu")]
    ])


def get_district_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора района.
    Районы можно легко изменить здесь без правки всего кода.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с районами
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏛 Центральный", callback_data="district_Центральный"),
            InlineKeyboardButton(text="🌅 Западный", callback_data="district_Западный")
        ],
        [
            InlineKeyboardButton(text="🌊 Прикубанский", callback_data="district_Прикубанский"),
            InlineKeyboardButton(text="🌳 Карасунский", callback_data="district_Карасунский")
        ],
        [
            InlineKeyboardButton(text="🌆 Фестивальный", callback_data="district_Фестивальный"),
            InlineKeyboardButton(text="🏭 Комсомольский", callback_data="district_Комсомольский")
        ],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="return_to_menu")]
    ])


def get_budget_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора бюджета.
    Диапазоны цен актуальны для рынка недвижимости.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с диапазонами цен
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💵 до 3 млн", callback_data="budget_0-3000000"),
            InlineKeyboardButton(text="💰 3-5 млн", callback_data="budget_3000000-5000000")
        ],
        [
            InlineKeyboardButton(text="💎 5-10 млн", callback_data="budget_5000000-10000000"),
            InlineKeyboardButton(text="👑 10-20 млн", callback_data="budget_10000000-20000000")
        ],
        [
            InlineKeyboardButton(text="🏰 20-50 млн", callback_data="budget_20000000-50000000"),
            InlineKeyboardButton(text="💸 50+ млн", callback_data="budget_50000000-999999999")
        ],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="return_to_menu")]
    ])


def get_rooms_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора количества комнат.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с вариантами количества комнат
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1️⃣ 1 комната", callback_data="rooms_1"),
            InlineKeyboardButton(text="2️⃣ 2 комнаты", callback_data="rooms_2"),
            InlineKeyboardButton(text="3️⃣ 3 комнаты", callback_data="rooms_3")
        ],
        [
            InlineKeyboardButton(text="4️⃣ 4 комнаты", callback_data="rooms_4"),
            InlineKeyboardButton(text="5️⃣ 5+ комнат", callback_data="rooms_5"),
            InlineKeyboardButton(text="❓ Не важно", callback_data="rooms_none")
        ],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="return_to_menu")]
    ])


def get_contact_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с контактной информацией.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с контактами
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✈️ Написать в Telegram", url="https://t.me/aleks8108")],
        [InlineKeyboardButton(text="📞 Позвонить", url="tel:+79054764448")],
        [InlineKeyboardButton(text="✉️ Написать Email", url="mailto:aleks8108@gmail.com")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="return_to_menu")]
    ])


def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для запроса номера телефона.
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопкой отправки контакта
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)],
            [KeyboardButton(text="✍️ Ввести номер вручную")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_menu_and_clear_buttons() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопками возврата в меню и очистки чата.
    
    Returns:
        InlineKeyboardMarkup: Служебная клавиатура
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="return_to_menu")],
        [InlineKeyboardButton(text="🗑 Очистить чат", callback_data="clear_chat")]
    ])


def get_listing_menu(
    listing_exists: bool,
    comments_provided: bool,
    has_next_listing: bool,
    listing_index: int,
    photo_index: int,
    total_photos: int,
    total_listings: int,
    listing_id: str
) -> InlineKeyboardMarkup:
    """
    Создает сложную клавиатуру для навигации по объектам недвижимости.
    
    Args:
        listing_exists: Есть ли объекты для показа
        comments_provided: Предоставлены ли комментарии
        has_next_listing: Есть ли следующий объект
        listing_index: Индекс текущего объекта
        photo_index: Индекс текущей фотографии
        total_photos: Общее количество фотографий
        total_listings: Общее количество объектов
        listing_id: ID текущего объекта
    
    Returns:
        InlineKeyboardMarkup: Клавиатура для навигации по объектам
    """
    if not isinstance(listing_index, int) or not isinstance(photo_index, int):
        logger.error(f"Некорректные индексы: listing_index={listing_index}, photo_index={photo_index}")
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="return_to_menu")]
        ])
    
    buttons = []
    
    if listing_exists:
        # Навигация по фотографиям
        photo_nav_buttons = []
        if total_photos > 1:
            if photo_index > 0:
                photo_nav_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️ Фото", 
                        callback_data=f"prev_photo_{listing_index}_{photo_index-1}"
                    )
                )
            
            # Показываем текущую позицию фотографии
            if total_photos > 1:
                photo_nav_buttons.append(
                    InlineKeyboardButton(
                        text=f"📸 {photo_index+1}/{total_photos}",
                        callback_data="photo_info"
                    )
                )
            
            if photo_index < total_photos - 1:
                photo_nav_buttons.append(
                    InlineKeyboardButton(
                        text="Фото ➡️", 
                        callback_data=f"next_photo_{listing_index}_{photo_index+1}"
                    )
                )
        
        if photo_nav_buttons:
            buttons.append(photo_nav_buttons)
        
        # Навигация по объектам
        listing_nav_buttons = []
        if total_listings > 1:
            if listing_index > 0:
                listing_nav_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️ Объект", 
                        callback_data=f"prev_listing_{listing_index-1}"
                    )
                )
            
            # Показываем текущую позицию объекта
            listing_nav_buttons.append(
                InlineKeyboardButton(
                    text=f"🏠 {listing_index+1}/{total_listings}",
                    callback_data="listing_info"
                )
            )
            
            if has_next_listing:
                listing_nav_buttons.append(
                    InlineKeyboardButton(
                        text="Объект ➡️", 
                        callback_data=f"next_listing_{listing_index+1}"
                    )
                )
        
        if listing_nav_buttons:
            buttons.append(listing_nav_buttons)
        
        # Кнопка интереса
        buttons.append([
            InlineKeyboardButton(
                text="❤️ Интересует", 
                callback_data=f"interested_{listing_id}"
            )
        ])
        
        # Если комментарии предоставлены, показываем кнопку завершения
        if comments_provided:
            buttons.append([
                InlineKeyboardButton(
                    text="✅ Завершить заявку", 
                    callback_data="finish_request"
                )
            ])
    
    # Системные кнопки
    system_buttons = []
    if not comments_provided:
        system_buttons.append(
            InlineKeyboardButton(
                text="🔍 Новый поиск", 
                callback_data="search"
            )
        )
    
    system_buttons.append(
        InlineKeyboardButton(
            text="🔙 В меню", 
            callback_data="return_to_menu"
        )
    )
    
    buttons.append(system_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для административной панели.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура административной панели
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика заявок", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Последние действия", callback_data="admin_actions")],
        [InlineKeyboardButton(text="📋 История заявок", callback_data="admin_requests")],
        [InlineKeyboardButton(text="🔄 Обновить данные", callback_data="admin_refresh")],
        [InlineKeyboardButton(text="🔙 Закрыть панель", callback_data="return_to_menu")]
    ])


def create_pagination_keyboard(
    current_page: int, 
    total_pages: int, 
    callback_pattern: str,
    additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None
) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с пагинацией для больших списков данных.
    
    Args:
        current_page: Текущая страница (начиная с 0)
        total_pages: Общее количество страниц
        callback_pattern: Шаблон для callback_data (должен содержать {page})
        additional_buttons: Дополнительные кнопки для добавления
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с пагинацией
    """
    buttons = []
    
    if additional_buttons:
        buttons.extend(additional_buttons)
    
    # Кнопки пагинации
    if total_pages > 1:
        pagination_buttons = []
        
        # Кнопка "Предыдущая"
        if current_page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="⬅️", 
                    callback_data=callback_pattern.format(page=current_page-1)
                )
            )
        
        # Информация о текущей странице
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{current_page+1}/{total_pages}",
                callback_data="page_info"
            )
        )
        
        # Кнопка "Следующая"
        if current_page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="➡️", 
                    callback_data=callback_pattern.format(page=current_page+1)
                )
            )
        
        buttons.append(pagination_buttons)
    
    # Кнопка возврата в меню
    buttons.append([
        InlineKeyboardButton(text="🔙 В главное меню", callback_data="return_to_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)