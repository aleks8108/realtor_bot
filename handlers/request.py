from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.sheets import save_request
from config import ADMIN_ID
from keyboards.search_filters import get_property_type_keyboard, get_deal_type_keyboard, get_district_keyboard, get_budget_keyboard, get_start_reply_keyboard
import logging

logging.basicConfig(level=logging.DEBUG)

router = Router()

def get_menu_and_clear_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="return_to_menu")],
        [InlineKeyboardButton(text="🗑 Очистить чат", callback_data="clear_chat")]
    ])

class RequestStates(StatesGroup):
    name = State()
    phone = State()
    property_type = State()
    deal_type = State()
    district = State()
    budget = State()
    comments = State()

@router.message(F.text == "📤 Оставить заявку")
async def start_request(message: types.Message, state: FSMContext):
    await message.answer("Введите ваше имя:")
    await state.set_state(RequestStates.name)

@router.message(RequestStates.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Введите ваш номер телефона (или отправьте контакт через Telegram):", 
                        reply_markup=types.ReplyKeyboardMarkup(
                            keyboard=[[types.KeyboardButton(text="📱 Отправить контакт", request_contact=True)]],
                            resize_keyboard=True,
                            one_time_keyboard=True
                        ))
    await state.set_state(RequestStates.phone)

@router.message(RequestStates.phone, F.contact | F.text)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text.strip()
    if not phone:
        await message.answer("Пожалуйста, отправьте номер телефона.")
        return
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.sheets import save_request
from config import ADMIN_ID
from keyboards.search_filters import get_property_type_keyboard, get_deal_type_keyboard, get_district_keyboard, get_budget_keyboard, get_start_reply_keyboard
import logging

logging.basicConfig(level=logging.DEBUG)

router = Router()

def get_menu_and_clear_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="return_to_menu")],
        [InlineKeyboardButton(text="🗑 Очистить чат", callback_data="clear_chat")]
    ])

class RequestStates(StatesGroup):
    name = State()
    phone = State()
    property_type = State()
    deal_type = State()
    district = State()
    budget = State()
    comments = State()

@router.message(F.text == "📤 Оставить заявку")
async def start_request(message: types.Message, state: FSMContext):
    await message.answer("Введите ваше имя:", reply_markup=get_menu_and_clear_buttons())
    await state.set_state(RequestStates.name)

@router.message(RequestStates.name)
async def process_name(message: types.Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("Пожалуйста, введите имя.", reply_markup=get_menu_and_clear_buttons())
        return
    await state.update_data(name=message.text.strip())
    await message.answer("Введите ваш номер телефона (или отправьте контакт через Telegram):",
                        reply_markup=types.ReplyKeyboardMarkup(
                            keyboard=[[types.KeyboardButton(text="📱 Отправить контакт", request_contact=True)]],
                            resize_keyboard=True,
                            one_time_keyboard=True
                        ))
    await state.set_state(RequestStates.phone)

@router.message(RequestStates.phone, F.contact | F.text)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text.strip()
    if not phone or not any(c.isdigit() for c in phone):
        await message.answer("Пожалуйста, введите корректный номер телефона.", reply_markup=get_menu_and_clear_buttons())
        return
    await state.update_data(phone=phone)
    await message.answer("Выберите тип недвижимости:", reply_markup=get_property_type_keyboard())
    await state.set_state(RequestStates.property_type)

@router.callback_query(RequestStates.property_type)
async def process_property_type(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(property_type=callback.data)
    await callback.message.edit_text("Выберите тип сделки:", reply_markup=get_deal_type_keyboard())
    await state.set_state(RequestStates.deal_type)
    await callback.answer()

@router.callback_query(RequestStates.deal_type)
async def process_deal_type(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(deal_type=callback.data)
    await callback.message.edit_text("Выберите район:", reply_markup=get_district_keyboard())
    await state.set_state(RequestStates.district)
    await callback.answer()

@router.callback_query(RequestStates.district)
async def process_district(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(district=callback.data)
    await callback.message.edit_text("Выберите бюджет:", reply_markup=get_budget_keyboard())
    await state.set_state(RequestStates.budget)
    await callback.answer()

@router.callback_query(RequestStates.budget)
async def process_budget(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(budget=callback.data)
    await callback.message.edit_text("Введите комментарии (или пропустите, нажав Enter):", reply_markup=get_menu_and_clear_buttons())
    await state.set_state(RequestStates.comments)
    await callback.answer()

@router.message(RequestStates.comments)
async def process_comments(message: types.Message, state: FSMContext):
    comments = message.text.strip() if message.text and message.text.strip() else "Без комментариев"
    await state.update_data(comments=comments)
    data = await state.get_data()
    
    try:
        save_request(data)
        text = (f"Новая заявка:\n"
                f"👤 Имя: {data['name']}\n"
                f"📞 Телефон: {data['phone']}\n"
                f"🏠 Тип недвижимости: {data['property_type']}\n"
                f"🤝 Сделка: {data['deal_type']}\n"
                f"📍 Район: {data['district']}\n"
                f"💰 Бюджет: {data['budget']}\n"
                f"📝 Комментарии: {data['comments']}")
        await message.bot.send_message(ADMIN_ID, text)
        await message.answer("Заявка успешно отправлена! Риэлтор свяжется с вами.",
                            reply_markup=get_start_reply_keyboard() if get_start_reply_keyboard else get_menu_and_clear_buttons())
    except Exception as e:
        logging.error(f"Ошибка при сохранении заявки: {e}")
        await message.answer("Ошибка при отправке заявки. Попробуйте позже.",
                            reply_markup=get_menu_and_clear_buttons())
    await state.clear()

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