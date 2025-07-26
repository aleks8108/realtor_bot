from aiogram import Router, types
from aiogram.filters import Command
from keyboards.main_menu import get_main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = "👋 Добро пожаловать в бот риэлтора!\nВыберите действие:"
    await message.answer(welcome_text, reply_markup=get_main_menu())