from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
    # Пример районов, можно расширить
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Центр", callback_data="Центр")],
        [InlineKeyboardButton(text="Север", callback_data="Север")],
        [InlineKeyboardButton(text="Юг", callback_data="Юг")],
        [InlineKeyboardButton(text="Запад", callback_data="Запад")],
        [InlineKeyboardButton(text="Восток", callback_data="Восток")]
    ])