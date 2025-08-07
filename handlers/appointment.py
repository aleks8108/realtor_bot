from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from services.sheets import save_appointment
from keyboards.search_filters import get_start_reply_keyboard
import logging

logging.basicConfig(level=logging.DEBUG)

router = Router()

def get_menu_and_clear_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="return_to_menu")],
        [InlineKeyboardButton(text="🗑 Очистить чат", callback_data="clear_chat")]
    ])

class AppointmentStates(StatesGroup):
    date = State()
    time = State()
    address = State()

@router.message(F.text == "📆 Назначить встречу")
async def start_appointment(message: types.Message, state: FSMContext):
    await message.answer("Введите дату встречи (например, 2025-07-28):", reply_markup=get_menu_and_clear_buttons())
    await state.set_state(AppointmentStates.date)

@router.message(AppointmentStates.date)
async def process_date(message: types.Message, state: FSMContext):
    date = message.text.strip()
    if not validate_date(date):
        await message.answer("Пожалуйста, введите дату в формате ГГГГ-ММ-ДД (например, 2025-07-28).", reply_markup=get_menu_and_clear_buttons())
        return
    await state.update_data(date=date)
    await message.answer("Введите время встречи (например, 14:00):", reply_markup=get_menu_and_clear_buttons())
    await state.set_state(AppointmentStates.time)

@router.message(AppointmentStates.time)
async def process_time(message: types.Message, state: FSMContext):
    time = message.text.strip()
    if not validate_time(time):
        await message.answer("Пожалуйста, введите время в формате ЧЧ:ММ (например, 14:00).", reply_markup=get_menu_and_clear_buttons())
        return
    await state.update_data(time=time)
    await message.answer("Введите адрес или описание объекта для встречи:", reply_markup=get_menu_and_clear_buttons())
    await state.set_state(AppointmentStates.address)

@router.message(AppointmentStates.address)
async def process_address(message: types.Message, state: FSMContext):
    address = message.text.strip() if message.text and message.text.strip() else "Не указан"
    await state.update_data(address=address)
    data = await state.get_data()

    try:
        save_appointment(data, message.from_user.full_name, message.from_user.id)
        text = (f"Новая заявка на встречу:\n"
                f"📅 Дата: {data['date']}\n"
                f"🕒 Время: {data['time']}\n"
                f"📍 Адрес/объект: {data['address']}\n"
                f"👤 Клиент: {message.from_user.full_name} (@{message.from_user.username or 'no_username'})\n"
                f"🆔 ID: {message.from_user.id}")
        await message.bot.send_message(ADMIN_ID, text)
        await message.answer("Встреча успешно назначена! Риэлтор свяжется с вами.",
                            reply_markup=get_start_reply_keyboard() if get_start_reply_keyboard else get_menu_and_clear_buttons())
    except Exception as e:
        logging.error(f"Ошибка при назначении встречи: {e}")
        await message.answer("Ошибка при назначении встречи. Попробуйте позже.",
                            reply_markup=get_menu_and_clear_buttons())
    await state.clear()

def validate_date(date: str) -> bool:
    try:
        from datetime import datetime
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_time(time: str) -> bool:
    try:
        from datetime import datetime
        datetime.strptime(time, "%H:%M")
        return True
    except ValueError:
        return False

@router.callback_query(lambda c: c.data == "return_to_menu")
async def return_to_menu(callback: types.CallbackQuery):
    try:
        keyboard = get_start_reply_keyboard() if get_start_reply_keyboard else get_menu_and_clear_buttons()
        await callback.message.edit_text("Вы вернулись в главное меню.", reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Ошибка при редактировании сообщения: {e}")
        await callback.message.answer("Не удалось обновить меню.", reply_markup=get_menu_and_clear_buttons())
    await callback.answer()

@router.callback_query(lambda c: c.data == "clear_chat")
async def clear_chat(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения: {e}")
    await callback.answer("Чат очищен.")