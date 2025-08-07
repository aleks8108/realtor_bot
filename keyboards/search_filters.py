from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_start_reply_keyboard():
       return InlineKeyboardMarkup(inline_keyboard=[
           [InlineKeyboardButton(text="🏠 Найти недвижимость", callback_data="search")],
           [InlineKeyboardButton(text="📤 Оставить заявку", callback_data="request")],
           [InlineKeyboardButton(text="📆 Назначить встречу", callback_data="appointment")],
           [InlineKeyboardButton(text="📞 Связаться с риэлтором", callback_data="contact")]
       ])

def get_property_type_keyboard():
       return InlineKeyboardMarkup(inline_keyboard=[
           [InlineKeyboardButton(text="Квартира", callback_data="property_type_Квартира")],
           [InlineKeyboardButton(text="Дом", callback_data="property_type_Дом")],
           [InlineKeyboardButton(text="Коммерческая", callback_data="property_type_Коммерческая")],
           [InlineKeyboardButton(text="Участок", callback_data="property_type_Участок")]
       ])

def get_deal_type_keyboard():
       return InlineKeyboardMarkup(inline_keyboard=[
           [InlineKeyboardButton(text="Аренда", callback_data="deal_type_Аренда")],
           [InlineKeyboardButton(text="Покупка", callback_data="deal_type_Покупка")]
       ])

def get_district_keyboard():
       return InlineKeyboardMarkup(inline_keyboard=[
           [InlineKeyboardButton(text="Центральный", callback_data="district_Центральный"),
            InlineKeyboardButton(text="Западный", callback_data="district_Западный"),
            InlineKeyboardButton(text="Прикубанский", callback_data="district_Прикубанский"),
            InlineKeyboardButton(text="Карасунский", callback_data="district_Карасунский")]
       ])

def get_budget_keyboard():
       return InlineKeyboardMarkup(inline_keyboard=[
           [InlineKeyboardButton(text="0-5 млн", callback_data="budget_0-5000000"),
            InlineKeyboardButton(text="5-10 млн", callback_data="budget_5000000-10000000"),
            InlineKeyboardButton(text="10-50 млн", callback_data="budget_10000000-50000000"),
            InlineKeyboardButton(text="50-100 млн", callback_data="budget_50000000-100000000")]
       ])