from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from keyboards.main_menu import get_main_menu
import logging

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
async def process_request(callback: CallbackQuery):
    await callback.message.answer("Переход к подаче заявки...", reply_markup=get_main_menu())
    await callback.answer()

@router.callback_query(lambda c: c.data == "appointment")
async def process_appointment(callback: CallbackQuery):
    await callback.message.answer("Переход к назначению встречи...", reply_markup=get_main_menu())
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

@router.callback_query(lambda c: c.data == "return_to_menu")
async def return_to_menu(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "Вы вернулись в главное меню.\nВыберите действие:",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
    await callback.answer()