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
from services.error_handler import handle_errors, ErrorHandler
from utils.keyboards import (
    create_main_keyboard, 
    create_property_keyboard, 
    create_navigation_keyboard
)
from exceptions.custom_exceptions import ServiceError

# Создаем роутер для обработчиков поиска
router = Router()

# Инициализируем сервисы
sheets_service = GoogleSheetsService()
listing_service = ListingService(sheets_service)
error_handler = ErrorHandler()

logger = logging.getLogger(__name__)


@router.message(F.text == "🔍 Поиск объектов")
@handle_errors(error_handler)
async def start_search(message: Message, state: FSMContext):
    """
    Начинает процесс поиска объектов недвижимости.
    Загружает все доступные объекты и показывает первый из них.
    """
    try:
        # Получаем все объекты недвижимости
        properties = await sheets_service.get_all_properties()
        
        if not properties:
            await message.reply(
                "😔 К сожалению, на данный момент нет доступных объектов.\n"
                "Попробуйте позже или свяжитесь с нашими менеджерами.",
                reply_markup=create_main_keyboard()
            )
            return
        
        # Сохраняем список объектов и текущий индекс в состоянии
        await state.update_data(
            properties=properties,
            current_index=0
        )
        
        # Показываем первый объект
        await show_property_at_index(message, state, 0, is_new_search=True)
        
        # Устанавливаем состояние просмотра
        await state.set_state(SearchStates.viewing_properties)
        
        logger.info(f"Пользователь {message.from_user.id} начал поиск. Найдено {len(properties)} объектов")
        
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
    Эта функция централизует логику отображения объектов и может использоваться
    как для новых поисков, так и для навигации между объектами.
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
    
    # Обновляем текущий индекс в состоянии
    await state.update_data(current_index=index)
    
    # Форматируем сообщение об объекте
    property_message = listing_service.format_property_message(
        current_property,
        index + 1,  # Номер для отображения (начинается с 1)
        len(properties)  # Общее количество объектов
    )
    
    # Создаем клавиатуру для текущего объекта
    keyboard = create_property_keyboard(
        property_id=current_property.get('id'),
        current_index=index,
        total_count=len(properties)
    )
    
    # Отправляем или редактируем сообщение в зависимости от контекста
    if edit_message:
        await message.edit_text(
            property_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    else:
        # Для нового поиска показываем информационное сообщение
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


@router.callback_query(F.data.startswith("nav_"))
@handle_errors(error_handler)
async def handle_navigation(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает навигацию между объектами недвижимости.
    Поддерживает переходы к следующему, предыдущему, первому и последнему объекту.
    """
    action = callback.data.split("_")[1]  # Извлекаем действие из callback_data
    
    data = await state.get_data()
    properties = data.get('properties', [])
    current_index = data.get('current_index', 0)
    
    if not properties:
        await callback.answer("❌ Нет доступных объектов", show_alert=True)
        return
    
    # Определяем новый индекс в зависимости от действия
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
    
    # Проверяем, не находимся ли мы уже на нужном объекте
    if new_index == current_index:
        # Даем пользователю понять, что он достиг границы списка
        if action in ["next", "last"] and current_index == len(properties) - 1:
            await callback.answer("📍 Это последний объект в списке")
        elif action in ["prev", "first"] and current_index == 0:
            await callback.answer("📍 Это первый объект в списке")
        else:
            await callback.answer()
        return
    
    # Показываем объект с новым индексом
    await show_property_at_index(
        callback.message, 
        state, 
        new_index, 
        edit_message=True
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("photo_"))
@handle_errors(error_handler)
async def handle_photo_navigation(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает навигацию по фотографиям текущего объекта.
    Позволяет пользователю просматривать все доступные фотографии объекта.
    """
    try:
        # Извлекаем ID объекта и номер фотографии из callback_data
        # Формат: "photo_123_1" где 123 - ID объекта, 1 - номер фотографии
        parts = callback.data.split("_")
        property_id = int(parts[1])
        photo_index = int(parts[2])
        
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка в данных фотографии", show_alert=True)
        return
    
    data = await state.get_data()
    properties = data.get('properties', [])
    current_index = data.get('current_index', 0)
    
    # Находим текущий объект
    current_property = None
    for prop in properties:
        if prop.get('id') == property_id:
            current_property = prop
            break
    
    if not current_property:
        await callback.answer("❌ Объект не найден", show_alert=True)
        return
    
    # Получаем фотографии объекта
    photos = listing_service.get_property_photos(current_property)
    
    if not photos or photo_index < 0 or photo_index >= len(photos):
        await callback.answer("❌ Фотография не найдена", show_alert=True)
        return
    
    try:
        # Отправляем фотографию пользователю
        photo_url = photos[photo_index]
        caption = (
            f"📸 Фотография {photo_index + 1} из {len(photos)}\n"
            f"🏠 {current_property.get('address', 'Адрес не указан')}"
        )
        
        # Создаем клавиатуру для навигации по фотографиям
        photo_keyboard = create_navigation_keyboard(
            property_id=property_id,
            current_photo=photo_index,
            total_photos=len(photos),
            keyboard_type="photo"
        )
        
        await callback.message.answer_photo(
            photo=photo_url,
            caption=caption,
            reply_markup=photo_keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка отправки фотографии: {e}")
        await callback.answer("❌ Ошибка загрузки фотографии", show_alert=True)


@router.callback_query(F.data == "back_to_list")
@handle_errors(error_handler)
async def back_to_property_list(callback: CallbackQuery, state: FSMContext):
    """
    Возвращает пользователя к списку объектов из режима просмотра фотографий
    или других детальных режимов просмотра.
    """
    data = await state.get_data()
    current_index = data.get('current_index', 0)
    
    # Показываем текущий объект
    await show_property_at_index(
        callback.message,
        state,
        current_index,
        edit_message=True
    )
    
    await callback.answer("🔙 Возврат к списку объектов")


@router.callback_query(F.data == "end_search")
@handle_errors(error_handler)
async def end_search(callback: CallbackQuery, state: FSMContext):
    """
    Завершает процесс поиска и возвращает пользователя в главное меню.
    Очищает все данные поиска из состояния FSM.
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


@router.message(SearchStates.viewing_properties)
@handle_errors(error_handler)
async def handle_text_during_search(message: Message, state: FSMContext):
    """
    Обрабатывает текстовые сообщения во время просмотра объектов.
    Предоставляет пользователю подсказки о том, как использовать интерфейс.
    """
    if message.text and message.text.lower() in ['выход', 'завершить', 'стоп']:
        await end_search(message, state)
        return
    
    # Показываем подсказку пользователю
    await message.reply(
        "💡 Используйте кнопки под сообщением для навигации по объектам.\n\n"
        "• ⬅️➡️ - переход между объектами\n"
        "• 📸 - просмотр фотографий\n"
        "• 📋 - подача заявки на просмотр\n"
        "• ❌ - завершение поиска\n\n"
        "Или напишите 'выход' для завершения поиска.",
        reply_markup=None
    )