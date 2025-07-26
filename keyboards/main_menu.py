from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Найти недвижимость")],
            [KeyboardButton(text="📤 Оставить заявку"), KeyboardButton(text="📆 Назначить встречу")],
            [KeyboardButton(text="❓ Задать вопрос"), KeyboardButton(text="📞 Связаться с риэлтором")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )