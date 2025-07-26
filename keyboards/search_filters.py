from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_property_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Квартира", callback_data="Квартира")],
        [InlineKeyboardButton(text="Дом", callback_data="Дом")],
        [InlineKeyboardButton(text="Коммерческая", callback_data="Коммерческая")],
        [InlineKeyboardButton(text="Участок", callback_data="Участок")]
    ])

def get_deal_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Аренда", callback_data="Аренда")],
        [InlineKeyboardButton(text="Покупка", callback_data="Покупка")]
    ])

def get_district_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Центр", callback_data="Центр")],
        [InlineKeyboardButton(text="Север", callback_data="Север")],
        [InlineKeyboardButton(text="Юг", callback_data="Юг")],
        [InlineKeyboardButton(text="Запад", callback_data="Запад")],
        [InlineKeyboardButton(text="Восток", callback_data="Восток")]
    ])

def get_budget_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1,000,000 - 5,000,000 руб.", callback_data="1000000-5000000")],
        [InlineKeyboardButton(text="5,000,000 - 10,000,000 руб.", callback_data="5000000-10000000")],
        [InlineKeyboardButton(text="Более 10,000,000 руб.", callback_data="10000000-999999999")]
    ])

def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться в главное меню", callback_data="return_to_main")]
    ])

def get_start_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Найти недвижимость", callback_data="search")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ])

def get_start_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Найти недвижимость")],
            [KeyboardButton(text="📋 Мои заявки"), KeyboardButton(text="📞 Связаться с риэлтором")]
        ],
        resize_keyboard=True
    )