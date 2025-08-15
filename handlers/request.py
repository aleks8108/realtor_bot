"""
Обработчик процесса подачи заявки на недвижимость.
Этот модуль управляет всем процессом заполнения данных заявки,
включая выбор параметров и отправку в Google Sheets.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state

from states.request import RequestStates
from services.sheets import GoogleSheetsService
from services.error_handler import error_handler
from utils.keyboards import get_deal_type_keyboard, get_district_keyboard, get_budget_keyboard, get_rooms_keyboard, get_menu_and_clear_buttons, get_property_type_keyboard
from handlers.admin import log_user_action
from exceptions.custom_exceptions import ServiceError

router = Router()
sheets_service = GoogleSheetsService()
logger = logging.getLogger(__name__)

@router.message(RequestStates.name)
@error_handler(operation_name="Ввод имени")
async def process_name(message: Message, state: FSMContext):
    """
    Обрабатывает ввод имени пользователя.
    Переходит к следующему этапу (ввод телефона).
    """
    await state.update_data(name=message.text)
    await state.set_state(RequestStates.phone)
    await message.reply("Введите ваш номер телефона:")
    log_user_action(message.from_user.id, message.from_user.username, f"Ввод имени: {message.text}")

@router.message(RequestStates.phone)
@error_handler(operation_name="Ввод телефона")
async def process_phone(message: Message, state: FSMContext):
    """
    Обрабатывает ввод номера телефона.
    Переходит к выбору типа недвижимости.
    """
    await state.update_data(phone=message.text)
    
    # Проверка и отладка состояния
    data = await state.get_data()
    logger.info(f"Данные состояния: {data}")
    
    # Проверка, есть ли property_id в данных состояния
    property_id = data.get('property_id')  # Используем .get() для избежания KeyError
    
    if not property_id:
        logger.warning(f"property_id не найден для пользователя {message.from_user.id}. Устанавливаем None.")
        await state.update_data(property_id=None)  # Устанавливаем None, если отсутствует
    
    await state.set_state(RequestStates.property_type)
    await message.reply("Выберите тип недвижимости:", reply_markup=get_property_type_keyboard())
    log_user_action(message.from_user.id, message.from_user.username, f"Ввод телефона: {message.text}")

@router.message(RequestStates.property_type)
@error_handler(operation_name="Выбор типа недвижимости")
async def process_property_type(message: Message, state: FSMContext):
    """
    Обрабатывает выбор типа недвижимости.
    Переходит к выбору типа сделки.
    """
    await state.update_data(property_type=message.text)
    await state.set_state(RequestStates.deal_type)
    await message.reply("Выберите тип сделки:", reply_markup=get_deal_type_keyboard())
    log_user_action(message.from_user.id, message.from_user.username, f"Выбор типа недвижимости: {message.text}")

# ... (остальной код остается без изменений)

@router.callback_query(F.data.startswith("request_"))
@error_handler(operation_name="Подача заявки на объект")
async def start_request_from_listing(callback: CallbackQuery, state: FSMContext):
    """
    Инициирует процесс подачи заявки на конкретный объект недвижимости.
    """
    property_id = callback.data.replace("request_", "")
    await state.update_data(property_id=property_id)
    await state.set_state(RequestStates.name)
    await callback.message.answer("Введите ваше имя:")
    await callback.answer("Начало подачи заявки...")
    logger.info(f"Пользователь {callback.from_user.id} начал подачу заявки на объект {property_id}")
    log_user_action(callback.from_user.id, callback.from_user.username, f"Подача заявки на объект {property_id}")