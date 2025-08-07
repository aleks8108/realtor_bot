from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Найти недвижимость", callback_data="search")],
        [InlineKeyboardButton(text="📤 Оставить заявку", callback_data="request")],
        [InlineKeyboardButton(text="📆 Назначить встречу", callback_data="appointment")],
        [InlineKeyboardButton(text="📞 Связаться с риэлтором", callback_data="contact")]
    ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    


