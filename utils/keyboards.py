"""
Модуль клавиатур для риэлторского бота.
Содержит функции для создания различных типов клавиатур с улучшенной обработкой ошибок
и более гибкой настройкой кнопок в зависимости от контекста.
"""

import logging
from typing import List, Optional, Tuple
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

logger = logging.getLogger(__name__)

def create_main_keyboard() -> InlineKeyboardMarkup:
    """
    Создает основную inline-клавиатуру с главными функциями бота.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="create_request")],
        [InlineKeyboardButton(text="📞 Связаться с риэлтором", callback_data="contact_realtor")],
        [InlineKeyboardButton(text="📊 Калькуляторы", callback_data="open_calculators")]
    ])

def create_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой отмены/возврата в меню.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="return_to_menu")]
    ])

def create_property_keyboard(property_types: List[Tuple[str, str]], callback_prefix: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора типа недвижимости.
    """
    buttons = []
    for i in range(0, len(property_types), 2):
        row = []
        for j in range(i, min(i + 2, len(property_types))):
            text, value = property_types[j]
            row.append(InlineKeyboardButton(
                text=text,
                callback_data=f"{callback_prefix}_{value}"
            ))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="return_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_menu() -> InlineKeyboardMarkup:
    return create_main_keyboard()

def get_start_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Оставить заявку")],
            [KeyboardButton(text="📞 Связаться с риэлтором")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def get_deal_type_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Покупка", callback_data="deal_type_Покупка"),
            InlineKeyboardButton(text="🏠 Аренда", callback_data="deal_type_Аренда")
        ]
    ])
    keyboard.inline_keyboard.extend(create_cancel_keyboard().inline_keyboard)
    return keyboard

def get_district_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏛 Центральный", callback_data="val_district_Центральный"),
            InlineKeyboardButton(text="🌅 Западный", callback_data="val_district_Западный")
        ],
        [
            InlineKeyboardButton(text="🌊 Прикубанский", callback_data="val_district_Прикубанский"),
            InlineKeyboardButton(text="🏞 Карасунский", callback_data="val_district_Карасунский")
        ]
    ])
    keyboard.inline_keyboard.extend(create_cancel_keyboard().inline_keyboard)
    return keyboard

def get_budget_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💵 до 5 млн", callback_data="budget_0-5000000"),
            InlineKeyboardButton(text="💸 5-10 млн", callback_data="budget_5000000-10000000")
        ],
        [
            InlineKeyboardButton(text="💰 10-50 млн", callback_data="budget_10000000-50000000"),
            InlineKeyboardButton(text="💎 50-100 млн", callback_data="budget_50000000-100000000")
        ],
        [
            InlineKeyboardButton(text="🔥 более 100 млн", callback_data="budget_100000000-1000000000")
        ]
    ])
    keyboard.inline_keyboard.extend(create_cancel_keyboard().inline_keyboard)
    return keyboard

def get_rooms_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1️⃣ 1 комната", callback_data="rooms_1"),
            InlineKeyboardButton(text="2️⃣ 2 комнаты", callback_data="rooms_2"),
            InlineKeyboardButton(text="3️⃣ 3 комнаты", callback_data="rooms_3")
        ],
        [
            InlineKeyboardButton(text="4️⃣ 4 комнаты", callback_data="rooms_4"),
            InlineKeyboardButton(text="5️⃣ 5+ комнат", callback_data="rooms_5"),
            InlineKeyboardButton(text="❓ Не важно", callback_data="rooms_none")
        ]
    ])
    keyboard.inline_keyboard.extend(create_cancel_keyboard().inline_keyboard)
    return keyboard

def get_menu_and_clear_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="return_to_menu")],
        [InlineKeyboardButton(text="🧹 Очистить чат", callback_data="clear_chat")]
    ])

def get_listing_menu(
    listing_exists: bool,
    comments_provided: bool = False,
    has_next_listing: bool = False,
    listing_index: int = 0,
    photo_index: int = 0,
    total_photos: int = 0,
    total_listings: int = 0,
    listing_id: Optional[str] = None
) -> InlineKeyboardMarkup:
    """
    Создает динамическую клавиатуру для взаимодействия с объектом недвижимости.
    """
    if not isinstance(listing_index, int) or not isinstance(photo_index, int):
        logger.error(
            f"Некорректные типы индексов: listing_index={type(listing_index)}, "
            f"photo_index={type(photo_index)}"
        )
        return get_main_menu()

    if listing_index < 0 or photo_index < 0:
        logger.error(f"Отрицательные индексы: listing_index={listing_index}, photo_index={photo_index}")
        return get_main_menu()

    if not listing_exists:
        return get_main_menu()

    buttons = []

    if listing_id:
        buttons.append([
            InlineKeyboardButton(text="📋 Подать заявку", callback_data=f"request_{listing_id}"),
            InlineKeyboardButton(text="❤️ Интересует", callback_data=f"interested_{listing_id}")
        ])

    if comments_provided:
        buttons.append([
            InlineKeyboardButton(text="✅ Завершить заявку", callback_data="finish_request")
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="return_to_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_contact_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с контактной информацией.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Отдел продаж", callback_data="show_sales_phone")],
        [InlineKeyboardButton(text="📞 Отдел аренды", callback_data="show_rent_phone")],
        [InlineKeyboardButton(text="📧 Email", callback_data="show_email")]
    ])

def get_admin_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Действия пользователей", callback_data="view_actions")],
        [InlineKeyboardButton(text="📊 Статистика заявок", callback_data="view_stats")],
        [InlineKeyboardButton(text="📋 История заявок", callback_data="view_requests")]
    ])
    keyboard.inline_keyboard.extend(create_cancel_keyboard().inline_keyboard)
    return keyboard

def create_confirmation_keyboard(
    confirm_callback: str,
    cancel_callback: str = "return_to_menu",
    confirm_text: str = "✅ Да",
    cancel_text: str = "❌ Нет"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=confirm_text, callback_data=confirm_callback),
            InlineKeyboardButton(text=cancel_text, callback_data=cancel_callback)
        ]
    ])

def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return create_cancel_keyboard()

def get_property_type_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора типа недвижимости.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏠 Квартира", callback_data="property_type_Квартира"),
            InlineKeyboardButton(text="🏡 Дом", callback_data="property_type_Дом")
        ],
        [
            InlineKeyboardButton(text="🏢 Коммерческая", callback_data="property_type_Коммерческая"),
            InlineKeyboardButton(text="🏢 Земельный участок", callback_data="property_type_Земельный участок")
        ],
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="return_to_menu")
        ]
    ])