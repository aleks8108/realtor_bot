"""
Обработчик поиска и просмотра объектов недвижимости.
Этот модуль управляет всем процессом поиска объектов, их отображения
и навигации между ними, используя централизованный сервис для работы с объектами.
"""

import logging
from typing import Optional, Dict, Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.search import SearchStates
from services.sheets import GoogleSheetsService
from services.listings import ListingService
from services.error_handler import error_handler
from utils.keyboards import create_main_keyboard, get_listing_menu, create_navigation_keyboard
from exceptions.custom_exceptions import ServiceError
from handlers.admin import log_user_action
from states.request import RequestStates
from utils.keyboards import get_property_type_keyboard, get_contact_keyboard

router = Router()

sheets_service = GoogleSheetsService()
logger = logging.getLogger(__name__)

@router.message(F.text == "🔍 Поиск объектов")
@error_handler(operation_name="Начало поиска объектов")
async def start_search(message: Message, state: FSMContext):
    """
    Начинает процесс поиска объектов недвижимости.
    Загружает все доступные объекты и показывает первый из них.
    """
    try:
        properties = await sheets_service.get_all_properties()
        
        if not properties:
            await message.reply(
                "😔 К сожалению, на данный момент нет доступных объектов.\n"
                "Попробуйте позже или свяжитесь с нашими менеджерами.",
                reply_markup=create_main_keyboard()
            )
            return
        
        await state.update_data(
            properties=properties,
            current_index=0
        )
        
        await show_property_at_index(message, state, 0, is_new_search=True)
        
        await state.set_state(SearchStates.viewing_listings)
        
        logger.info(f"Пользователь {message.from_user.id} начал поиск. Найдено {len(properties)} объектов")
        log_user_action(message.from_user.id, message.from_user.username, "Начало поиска объектов")
        
    except ServiceError as e:
        logger.error(f"Ошибка при загрузке объектов: {e}")
        await message.reply(
            "❌ Произошла ошибка при загрузке объектов. Попробуйте позже.",
            reply_markup=create_main_keyboard()
        )

async def show_property_at_index(
    message: Message, 
    state: FSMContext, 
    index: int, 
    is_new_search: bool = False,
    edit_message: bool = False
):
    """
    Показывает объект недвижимости по указанному индексу.
    """
    data = await state.get_data()
    properties = data.get('properties', [])
    
    if not properties or index < 0 or index >= len(properties):
        await message.reply(
            "❌ Объект не найден.",
            reply_markup=create_main_keyboard()
        )
        return
    
    current_property = properties[index]
    
    await state.update_data(current_index=index)
    
    property_message = ListingService._format_listing_message(
        current_property,
        index + 1,
        len(properties)
    )
    
    keyboard = get_listing_menu(
        listing_exists=True,
        comments_provided=False,
        has_next_listing=index < len(properties) - 1,
        listing_index=index,
        photo_index=0,
        total_photos=len(ListingService.get_property_photos(current_property)),
        total_listings=len(properties),
        listing_id=str(current_property.get('id'))
    )
    
    if edit_message:
        await message.edit_text(
            property_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    else:
        if is_new_search:
            intro_message = (
                f"🏠 Найдено <b>{len(properties)}</b> объектов недвижимости\n\n"
                f"Используйте кнопки для навигации между объектами:"
            )
            await message.reply(intro_message, parse_mode='HTML')
        
        await message.reply(
            property_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    log_user_action(message.from_user.id, message.from_user.username, f"Просмотр объекта #{index + 1}")

# Обработчики callback_query
@router.callback_query(F.data == "search_property")
@error_handler(operation_name="Запуск поиска через инлайн-кнопку")
async def process_search_property(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие инлайн-кнопки '🔍 Поиск недвижимости'.
    Запускает процесс поиска с начальным состоянием.
    """
    await state.set_state(SearchStates.awaiting_property_type)
    await callback.message.answer(
        "Выберите тип недвижимости:",
        reply_markup=get_property_type_keyboard()
    )
    await callback.answer("Начало поиска...")
    logger.info(f"Пользователь {callback.from_user.id} запустил поиск через инлайн-кнопку")

@router.callback_query(F.data == "create_request")
@error_handler(operation_name="Запуск подачи заявки через инлайн-кнопку")
async def process_create_request(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие инлайн-кнопки '📝 Оставить заявку'.
    Переходит к началу процесса подачи заявки.
    """
    await state.set_state(RequestStates.name)
    await callback.message.answer("Введите ваше имя:")
    await callback.answer("Начало подачи заявки...")
    logger.info(f"Пользователь {callback.from_user.id} начал подачу заявки")

@router.callback_query(F.data == "contact_realtor")
@error_handler(operation_name="Показ контактов через инлайн-кнопку")
async def process_contact_realtor(callback: CallbackQuery):
    """
    Обрабатывает нажатие инлайн-кнопки '📞 Связаться с риэлтором'.
    Отображает контактную информацию.
    """
    contacts_message = (
        f"📞 <b>Контактная информация</b>\n\n"
        f"🏢 <b>Наша компания</b>\n"
        f"Агентство недвижимости 'ДомСервис'\n\n"
        f"📱 <b>Телефоны:</b>\n"
        f"• Отдел продаж: +7 (XXX) XXX-XX-XX\n"
        f"• Отдел аренды: +7 (XXX) XXX-XX-XX\n"
        f"• Контактный номер: +7 905 476 44 48\n\n"
        f"🕐 <b>Режим работы:</b>\n"
        f"Пн-Пт: 9:00 - 19:00\n"
        f"Сб-Вс: 10:00 - 17:00\n\n"
        f"📍 <b>Адрес офиса:</b>\n"
        f"г. Москва, ул. Примерная, д. 123\n\n"
        f"💬 Напишите в Telegram: <a href='https://t.me/aleks8108'>@aleks8108</a>\n"
        f"📧 Напишите email: <a href='mailto:aleks8108@gmail.com'>aleks8108@gmail.com</a>"
    )
    await callback.message.answer(
        contacts_message,
        reply_markup=None,  # Убрана клавиатура
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    await callback.answer("Контакты показаны")
    logger.info(f"Пользователь {callback.from_user.id} запросил контакты")

@router.callback_query(F.data.startswith("nav_"))
@error_handler(operation_name="Навигация по объектам")
async def handle_navigation(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает навигацию между объектами недвижимости.
    """
    action = callback.data.split("_")[1]
    
    data = await state.get_data()
    properties = data.get('properties', [])
    current_index = data.get('current_index', 0)
    
    if not properties:
        await callback.answer("❌ Нет доступных объектов", show_alert=True)
        return
    
    if action == "next":
        new_index = min(current_index + 1, len(properties) - 1)
    elif action == "prev":
        new_index = max(current_index - 1, 0)
    elif action == "first":
        new_index = 0
    elif action == "last":
        new_index = len(properties) - 1
    else:
        await callback.answer("❌ Неизвестное действие", show_alert=True)
        return
    
    if new_index == current_index:
        if action in ["next", "last"] and current_index == len(properties) - 1:
            await callback.answer("📍 Это последний объект в списке")
        elif action in ["prev", "first"] and current_index == 0:
            await callback.answer("📍 Это первый объект в списке")
        else:
            await callback.answer()
        return
    
    await show_property_at_index(
        callback.message, 
        state, 
        new_index, 
        edit_message=True
    )
    
    await callback.answer()
    log_user_action(callback.from_user.id, callback.from_user.username, f"Навигация к объекту #{new_index + 1}")

@router.callback_query(F.data.startswith("photo_"))
@error_handler(operation_name="Навигация по фотографиям")
async def handle_photo_navigation(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает навигацию по фотографиям текущего объекта.
    """
    try:
        parts = callback.data.split("_")
        property_id = int(parts[1])
        photo_index = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка в данных фотографии", show_alert=True)
        return
    
    data = await state.get_data()
    properties = data.get('properties', [])
    
    current_property = None
    for prop in properties:
        if prop.get('id') == property_id:
            current_property = prop
            break
    
    if not current_property:
        await callback.answer("❌ Объект не найден", show_alert=True)
        return
    
    photos = ListingService.get_property_photos(current_property)
    
    if not photos or photo_index < 0 or photo_index >= len(photos):
        await callback.answer("❌ Фотография не найдена", show_alert=True)
        return
    
    try:
        photo_url = photos[photo_index]
        caption = (
            f"📸 Фотография {photo_index + 1} из {len(photos)}\n"
            f"🏠 {current_property.get('address', 'Адрес не указан')}"
        )
        
        nav_config = {
            'current_page': 0,
            'total_pages': 1,
            'has_prev': False,
            'has_next': False,
            'photo_index': photo_index,
            'total_photos': len(photos),
            'callback_prefix': f"photo_{property_id}",
            'keyboard_type': 'photo'
        }
        
        photo_keyboard = create_navigation_keyboard(nav_config)
        
        await callback.message.answer_photo(
            photo=photo_url,
            caption=caption,
            reply_markup=photo_keyboard
        )
        
        await callback.answer()
        log_user_action(callback.from_user.id, callback.from_user.username, f"Просмотр фото #{photo_index + 1} объекта ID: {property_id}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки фотографии: {e}")
        await callback.answer("❌ Ошибка загрузки фотографии", show_alert=True)

@router.callback_query(F.data == "back_to_list")
@error_handler(operation_name="Возврат к списку объектов")
async def back_to_property_list(callback: CallbackQuery, state: FSMContext):
    """
    Возвращает пользователя к списку объектов из режима просмотра фотографий.
    """
    data = await state.get_data()
    current_index = data.get('current_index', 0)
    
    await show_property_at_index(
        callback.message,
        state,
        current_index,
        edit_message=True
    )
    
    await callback.answer("🔙 Возврат к списку объектов")
    log_user_action(callback.from_user.id, callback.from_user.username, "Возврат к списку объектов")

@router.callback_query(F.data == "end_search")
@error_handler(operation_name="Завершение поиска")
async def end_search(callback: CallbackQuery, state: FSMContext):
    """
    Завершает процесс поиска и возвращает пользователя в главное меню.
    """
    await state.clear()
    
    await callback.message.edit_text(
        "✅ Поиск завершен.\n\n"
        "Спасибо за интерес к нашим объектам! "
        "Если у вас есть вопросы или вы хотите подать заявку на просмотр, "
        "воспользуйтесь соответствующими функциями бота.",
        reply_markup=create_main_keyboard()
    )
    
    await callback.answer()
    log_user_action(callback.from_user.id, callback.from_user.username, "Завершение поиска")

@router.message(SearchStates.viewing_listings)
@error_handler(operation_name="Обработка текста во время поиска")
async def handle_text_during_search(message: Message, state: FSMContext):
    """
    Обрабатывает текстовые сообщения во время просмотра объектов.
    """
    if message.text and message.text.lower() in ['выход', 'завершить', 'стоп']:
        await end_search(message, state)
        return
    
    await message.reply(
        "💡 Используйте кнопки под сообщением для навигации по объектам.\n\n"
        "• ⬅️➡️ - переход между объектами\n"
        "• 📸 - просмотр фотографий\n"
        "• 📋 - подача заявки на просмотр\n"
        "• ❌ - завершение поиска\n\n"
        "Или напишите 'выход' для завершения поиска.",
        reply_markup=None
    )
    log_user_action(message.from_user.id, message.from_user.username, "Ввод текста во время поиска")