from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards.search_filters import get_start_reply_keyboard
import logging

router = Router()

@router.message(Command("start"))
async def start_command(message: types.Message):
    logging.info(f"Команда /start вызвана пользователем {message.from_user.id}")
    await message.answer(
        "Добро пожаловать в YouMaklerBot! Я помогу вам найти недвижимость или связаться с риэлтором.",
        reply_markup=get_start_reply_keyboard()
    )

@router.message(lambda message: message.text == "📋 Мои заявки")
async def my_requests(message: types.Message):
    logging.info(f"Кнопка 'Мои заявки' нажата пользователем {message.from_user.id}")
    await message.answer("Ваши заявки пока недоступны. Эта функция в разработке.")

@router.message(lambda message: message.text == "📞 Связаться с риэлтором")
async def contact_realtor(message: types.Message):
    logging.info(f"Кнопка 'Связаться с риэлтором' нажата пользователем {message.from_user.id}")
    await message.answer("Свяжитесь с нами: 📞 +7 (999) 123-45-67, ✉️ info@youmakler.ru")