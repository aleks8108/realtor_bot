
"""
Обработчик процесса подачи заявок на недвижимость.
Этот модуль координирует весь процесс от начала подачи заявки до ее завершения,
используя улучшенную архитектуру с централизованными сервисами и обработкой ошибок.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ADMIN_ID
import logging
import asyncio
from datetime import datetime
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

#from realtor_bot.config import ADMIN_ID
from states.request import RequestStates
from services.sheets import GoogleSheetsService
from services.listings import ListingService
from services.error_handler import handle_error, ErrorHandler
from utils.keyboards import create_main_keyboard, create_cancel_keyboard
from utils.validators import validate_phone, validate_name
from exceptions.custom_exceptions import ValidationError, ServiceError

# Создаем роутер для обработчиков заявок
router = Router()

# Инициализируем сервисы
sheets_service = GoogleSheetsService()
listing_service = ListingService(sheets_service)
error_handler = ErrorHandler()

logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("request_"))
@handle_error(error_handler)
async def handle_request_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик начала процесса подачи заявки.
    Извлекает ID объекта из callback_data и начинает процесс сбора информации.
    """
    # Извлекаем ID объекта из callback_data (формат: "request_123")
    try:
        property_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка в данных объекта", show_alert=True)
        return

    # Получаем информацию об объекте для отображения пользователю
    property_info = await sheets_service.get_property_by_id(property_id)
    if not property_info:
        await callback.answer("❌ Объект не найден", show_alert=True)
        return

    # Сохраняем информацию об объекте в состоянии FSM
    await state.update_data(
        property_id=property_id,
        property_info=property_info
    )

    # Формируем сообщение с информацией об объекте
    property_message = listing_service.format_property_message(property_info)
    
    await callback.message.edit_text(
        f"{property_message}\n\n"
        f"📋 <b>Подача заявки на просмотр</b>\n\n"
        f"Для подачи заявки, пожалуйста, введите ваше имя:",
        reply_markup=create_cancel_keyboard(),
        parse_mode='HTML'
    )
    
    # Переходим к следующему состоянию
    await state.set_state(RequestStates.waiting_for_name)
    await callback.answer()


@router.message(RequestStates.waiting_for_name)
@handle_error(error_handler)
async def process_name(message: Message, state: FSMContext):
    """
    Обработчик ввода имени пользователя.
    Валидирует введенное имя и переходит к запросу номера телефона.
    """
    name = message.text.strip()
    
    # Проверка на команду отмены
    if name.lower() in ['/cancel', 'отмена']:
        await cancel_request(message, state)
        return
    
    # Валидируем введенное имя
    try:
        validate_name(name)
    except ValidationError as e:
        await message.reply(
            f"❌ {str(e)}\n\nПожалуйста, введите корректное имя:",
            reply_markup=create_cancel_keyboard()
        )
        return
    
    # Сохраняем имя в состоянии
    await state.update_data(user_name=name)
    
    await message.reply(
        f"✅ Спасибо, {name}!\n\n"
        f"📱 Теперь введите ваш номер телефона для связи:\n"
        f"(в формате +7XXXXXXXXXX или 8XXXXXXXXXX)",
        reply_markup=create_cancel_keyboard()
    )
    
    await state.set_state(RequestStates.waiting_for_phone)


@router.message(RequestStates.waiting_for_phone)
@handle_error(error_handler)
async def process_phone(message: Message, state: FSMContext):
    """
    Обработчик ввода номера телефона.
    Валидирует номер телефона и завершает процесс подачи заявки.
    """
    phone = message.text.strip()
    
    # Проверка на команду отмены
    if phone.lower() in ['/cancel', 'отмена']:
        await cancel_request(message, state)
        return
    
    # Валидируем номер телефона
    try:
        normalized_phone = validate_phone(phone)
    except ValidationError as e:
        await message.reply(
            f"❌ {str(e)}\n\n"
            f"Пожалуйста, введите корректный номер телефона:",
            reply_markup=create_cancel_keyboard()
        )
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    
    # Подготавливаем данные для сохранения заявки
    request_data = {
        'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'user_id': message.from_user.id,
        'username': message.from_user.username or 'Не указан',
        'user_name': data['user_name'],
        'phone': normalized_phone,
        'property_id': data['property_id'],
        'property_address': data['property_info'].get('address', 'Не указан')
    }
    
    try:
        # Сохраняем заявку в Google Sheets
        await sheets_service.save_request(request_data)
        
        # Формируем сообщение об успешной подаче заявки
        success_message = (
            f"✅ <b>Заявка успешно подана!</b>\n\n"
            f"📋 <b>Ваши данные:</b>\n"
            f"👤 Имя: {data['user_name']}\n"
            f"📱 Телефон: {normalized_phone}\n"
            f"🏠 Объект: {data['property_info'].get('address', 'Не указан')}\n\n"
            f"⏰ Наш менеджер свяжется с вами в ближайшее время для согласования времени просмотра.\n\n"
            f"Спасибо за интерес к нашим объектам!"
        )
        
        await message.reply(
            success_message,
            reply_markup=create_main_keyboard(),
            parse_mode='HTML'
        )
        
        # Отправляем уведомление администратору
        await notify_admin_about_request(message, request_data, data['property_info'])
        
        logger.info(f"Заявка успешно обработана от пользователя {message.from_user.id}")
        
    except ServiceError as e:
        logger.error(f"Ошибка при сохранении заявки: {e}")
        await message.reply(
            f"❌ Произошла ошибка при подаче заявки. Попробуйте еще раз или свяжитесь с поддержкой.",
            reply_markup=create_main_keyboard()
        )
    
    # Очищаем состояние после завершения процесса
    await state.clear()


async def notify_admin_about_request(message: Message, request_data: dict, property_info: dict):
    """
    Отправляет уведомление администратору о новой заявке.
    Эта функция изолирована для лучшего тестирования и повторного использования.
    """
    if not ADMIN_ID:
        return
    
    try:
        admin_message = (
            f"🔥 <b>Новая заявка на просмотр!</b>\n\n"
            f"👤 <b>Клиент:</b>\n"
            f"• ID: {request_data['user_id']}\n"
            f"• Username: @{request_data['username']}\n"
            f"• Имя: {request_data['user_name']}\n"
            f"• Телефон: {request_data['phone']}\n\n"
            f"🏠 <b>Объект:</b>\n"
            f"• ID: {request_data['property_id']}\n"
            f"• Адрес: {request_data['property_address']}\n"
            f"• Цена: {property_info.get('price', 'Не указана')}\n\n"
            f"⏰ Время подачи: {request_data['timestamp']}"
        )
        
        await message.bot.send_message(
            ADMIN_ID,
            admin_message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления администратору: {e}")


@router.callback_query(F.data == "cancel_request")
@handle_error(error_handler)
async def cancel_request_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик отмены заявки через callback кнопку"""
    await cancel_request(callback.message, state, is_callback=True)
    await callback.answer()


async def cancel_request(message: Message, state: FSMContext, is_callback: bool = False):
    """
    Универсальная функция отмены процесса подачи заявки.
    Может быть вызвана как из текстового сообщения, так и из callback.
    """
    await state.clear()
    
    cancel_message = (
        f"❌ Подача заявки отменена.\n\n"
        f"Вы можете начать заново или выбрать другой объект."
    )
    
    if is_callback:
        await message.edit_text(
            cancel_message,
            reply_markup=create_main_keyboard()
        )
    else:
        await message.reply(
            cancel_message,
            reply_markup=create_main_keyboard()
        )


@router.message(F.text.lower().in_(['отмена', '/cancel']))
@handle_error(error_handler)
async def handle_cancel_command(message: Message, state: FSMContext):
    """
    Обработчик команд отмены в любом состоянии.
    Позволяет пользователю выйти из процесса подачи заявки в любой момент.
    """
    current_state = await state.get_state()
    
    if current_state and current_state.startswith('RequestStates'):
        await cancel_request(message, state)
    else:
        await message.reply(
            "Нет активных процессов для отмены.",
            reply_markup=create_main_keyboard()
        )