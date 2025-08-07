from aiogram import Router
from aiogram.types import CallbackQuery  # Добавлен импорт

router = Router()

@router.callback_query(lambda c: c.data == "admin")
async def process_admin(callback: CallbackQuery):  # Исправлен тип
    await callback.message.answer("Функция админа в разработке.")
    await callback.answer()