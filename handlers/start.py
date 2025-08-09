# Файл: handlers/start.py

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.keyboards import get_main_menu, get_menu_and_clear_buttons  # Добавлен импорт
from states.request import RequestStates  # Добавлен импорт (для ошибки 3)
import logging

logging.basicConfig(level=logging.DEBUG)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать в бот по недвижимости!\nВыберите действие:",
        reply_markup=get_main_menu()
    )

@router.message(F.text == "📞 Связаться с риэлтором")
async def contact_realtor(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Написать в Telegram", url="https://t.me/aleks8108")]
    ])
    await message.answer(
        "Свяжитесь с риэлтором:\n📞 +7 (905) 476-44-48\n📧 Email: aleks8108@gmail.com",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data == "request")
async def process_request(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Обработан callback 'request' от пользователя {callback.from_user.id}")
    await callback.message.answer("Начало подачи заявки. Введите ваше имя:", reply_markup=get_menu_and_clear_buttons())
    await state.set_state(RequestStates.name)
    await callback.answer()

@router.callback_query(lambda c: c.data == "contact")
async def process_contact(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Написать в Telegram", url="https://t.me/aleks8108")]
    ])
    await callback.message.answer(
        "Свяжитесь с риэлтором:\n📞 +7 (905) 476-44-48\n📧 Email: aleks8108@gmail.com",
        reply_markup=keyboard
    )
    await callback.answer()

# Файл: handlers/start.py
@router.callback_query(lambda c: c.data == "return_to_menu")
async def return_to_menu(callback: CallbackQuery, state: FSMContext):
    try:
        # Проверяем, можно ли отредактировать сообщение
        message = callback.message
        if not message.text and not message.caption:  # Если нет текста или подписи
            await callback.message.answer(
                "Вы вернулись в главное меню.\nВыберите действие:",
                reply_markup=get_main_menu()
            )
        else:
            await callback.message.edit_text(
                "Вы вернулись в главное меню.\nВыберите действие:",
                reply_markup=get_main_menu()
            )
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            await callback.message.answer(
                "Вы вернулись в главное меню.\nВыберите действие:",
                reply_markup=get_main_menu()
            )
    await state.clear()
    await callback.answer()