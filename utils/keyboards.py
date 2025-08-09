import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    """
    Создаёт основное меню (inline-клавиатура).
    :return: InlineKeyboardMarkup
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="request")],
        [InlineKeyboardButton(text="📞 Связаться с риэлтором", callback_data="contact")],
        [InlineKeyboardButton(text="🔍 Поиск недвижимости", callback_data="search")]
    ])

def get_start_reply_keyboard():
    """
    Создаёт reply-клавиатуру для начального меню (аналог get_main_menu).
    :return: ReplyKeyboardMarkup
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Оставить заявку")],
            [KeyboardButton(text="📞 Связаться с риэлтором")],
            [KeyboardButton(text="🔍 Поиск недвижимости")]
        ],
        resize_keyboard=True
    )

def get_property_type_keyboard():
    """
    Создаёт inline-клавиатуру для выбора типа недвижимости.
    :return: InlineKeyboardMarkup
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Квартира", callback_data="property_type_Квартира"),
         InlineKeyboardButton(text="Дом", callback_data="property_type_Дом")],
        [InlineKeyboardButton(text="Коммерческая", callback_data="property_type_Коммерческая"),
         InlineKeyboardButton(text="Земельный участок", callback_data="property_type_Земельный участок")]
    ])

def get_deal_type_keyboard():
    """
    Создаёт inline-клавиатуру для выбора типа сделки.
    :return: InlineKeyboardMarkup
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Покупка", callback_data="deal_type_Покупка"),
         InlineKeyboardButton(text="Аренда", callback_data="deal_type_Аренда")]
    ])

def get_district_keyboard():
    """
    Создаёт inline-клавиатуру для выбора района.
    :return: InlineKeyboardMarkup
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Центральный", callback_data="district_Центральный"),
         InlineKeyboardButton(text="Западный", callback_data="district_Западный")],
        [InlineKeyboardButton(text="Прикубанский", callback_data="district_Прикубанский"),
         InlineKeyboardButton(text="Карасунский", callback_data="district_Карасунский")]
    ])

def get_budget_keyboard():
    """
    Создаёт inline-клавиатуру для выбора бюджета.
    :return: InlineKeyboardMarkup
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="0-5 млн", callback_data="budget_0-5000000"),
         InlineKeyboardButton(text="5-10 млн", callback_data="budget_5000000-10000000")],
        [InlineKeyboardButton(text="10-50 млн", callback_data="budget_10000000-50000000"),
         InlineKeyboardButton(text="50-100 млн", callback_data="budget_50000000-100000000")]
    ])

def get_rooms_keyboard():
    """
    Создаёт inline-клавиатуру для выбора количества комнат.
    :return: InlineKeyboardMarkup
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 комната", callback_data="rooms_1"),
         InlineKeyboardButton(text="2 комнаты", callback_data="rooms_2"),
         InlineKeyboardButton(text="3 комнаты", callback_data="rooms_3")],
        [InlineKeyboardButton(text="4 комнаты", callback_data="rooms_4"),
         InlineKeyboardButton(text="5 комнат", callback_data="rooms_5"),
         InlineKeyboardButton(text="Не выбрано", callback_data="rooms_none")]
    ])

def get_menu_and_clear_buttons():
    """
    Создаёт клавиатуру с кнопками "Главное меню" и "Очистить чат".
    :return: InlineKeyboardMarkup
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Главное меню", callback_data="return_to_menu")],
        [InlineKeyboardButton(text="Очистить чат", callback_data="clear_chat")]
    ])

def get_listing_menu(listing_exists, comments_provided, has_next_listing, listing_index, photo_index, total_photos, total_listings, listing_id):
    """
    Создаёт клавиатуру для отображения объекта недвижимости.
    :param listing_exists: Существует ли объект.
    :param comments_provided: Был ли введён комментарий.
    :param has_next_listing: Есть ли следующий объект.
    :param listing_index: Индекс текущего объекта.
    :param photo_index: Индекс текущей фотографии.
    :param total_photos: Общее количество фотографий.
    :param total_listings: Общее количество объектов.
    :param listing_id: ID объекта.
    :return: InlineKeyboardMarkup
    """
    buttons = []
    if not isinstance(listing_index, int) or not isinstance(photo_index, int):
        logging.error(f"Некорректные индексы: listing_index={listing_index}, photo_index={photo_index}")
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 В меню", callback_data="return_to_menu")]])

    if listing_exists:
        if comments_provided:
            buttons.append([InlineKeyboardButton(text="Завершить заявку", callback_data="finish_request")])
        if photo_index > 0:
            buttons.append([InlineKeyboardButton(text="⬅️ Пред фото", callback_data=f"prev_photo_{listing_index}_{photo_index-1}")])
        if photo_index < total_photos - 1:
            buttons.append([InlineKeyboardButton(text="➡️ След фото", callback_data=f"next_photo_{listing_index}_{photo_index+1}")])
        if has_next_listing:
            buttons.append([InlineKeyboardButton(text="➡️ След объект", callback_data=f"next_listing_{listing_index+1}")])
        if listing_index > 0:
            buttons.append([InlineKeyboardButton(text="⬅️ Пред объект", callback_data=f"prev_listing_{listing_index-1}")])
        buttons.append([InlineKeyboardButton(text="Интересует", callback_data=f"interested_{listing_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 В меню", callback_data="return_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)