from aiogram import Router
from aiogram.types import CallbackQuery  # Добавлен импорт

router = Router()

@router.callback_query(lambda c: c.data == "chat")
async def process_chat(callback: CallbackQuery):  # Исправлен тип
    await callback.message.answer("Функция чата в разработке.")
    await callback.answer()