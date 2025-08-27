"""
Обработчик заявок на просмотр недвижимости.
Обрабатывает пошаговый процесс создания заявки пользователя.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Contact, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from exceptions.custom_exceptions import ValidationError
from states.request import RequestStates
from utils.keyboards import (
    get_property_type_keyboard, get_deal_type_keyboard, get_district_keyboard,
    get_budget_keyboard, get_rooms_keyboard, get_listing_menu, get_main_menu
)
from services.listings import ListingService
from services.sheets import google_sheets_service
from config import ADMIN_ID
from utils.validators import validate_phone, validate_name
import logging
import re
from datetime import datetime, timezone, timedelta

router = Router()
logger = logging.getLogger(__name__)

# Обработчик команды /cancel
@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext):
    """
    Обработчик команды /cancel.
    Сбрасывает текущее состояние и возвращает пользователя в главное меню.
    """
    await state.clear()
    await message.answer("Действие отменено. Возвращаю вас в главное меню.", reply_markup=get_main_menu())
    logger.info(f"ID: {message.from_user.id} (@{message.from_user.username}) - Отменено текущее действие")

# Обработчик возврата в главное меню (кнопка)
@router.callback_query(F.data == "return_to_menu")
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки 'Главное меню'.
    Сбрасывает текущее состояние и возвращает пользователя в главное меню.
    """
    await state.clear()
    await callback.message.edit_text("Вы вернулись в главное меню.", reply_markup=get_main_menu())
    logger.info(f"ID: {callback.from_user.id} (@{callback.from_user.username}) - Возврат в главное меню")
    await callback.answer()

# Обработчик начала ввода имени
@router.message(StateFilter(RequestStates.name))
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    try:
        validated_name = validate_name(name)
        await state.update_data(name=validated_name)
        logger.info(f"ID: {message.from_user.id} (@{message.from_user.username}) - Ввод имени: {validated_name} - {message.date}")
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="📱 Отправить контакт", request_contact=True))
        builder.adjust(1)
        await message.answer("Введите номер телефона (например, +7 999 123 45 67) или отправьте контакт:",
                             reply_markup=builder.as_markup(resize_keyboard=True,
                                                           input_field_placeholder="Введите в формате +7 XXX XXX XX XX"))
        await state.set_state(RequestStates.phone)
    except ValidationError as e:
        logger.error(f"Ошибка валидации имени: {str(e)}")
        await message.answer(f"⚠️ {str(e)}! Пожалуйста, введите корректное имя (2-50 символов, только буквы, пробелы и дефисы).\nПопробуйте снова.")

# Обработчик ввода телефона или получения контакта
@router.message(StateFilter(RequestStates.phone))
async def process_phone(message: Message, state: FSMContext):
    phone = None
    if isinstance(message.contact, Contact):
        phone = message.contact.phone_number
        logger.info(f"ID: {message.from_user.id} (@{message.from_user.username}) - Получен контакт: {phone} - {message.date}")
    else:
        phone = message.text.strip()
        logger.info(f"ID: {message.from_user.id} (@{message.from_user.username}) - Ввод телефона: {phone} - {message.date}")

    try:
        validated_phone = validate_phone(phone)
        await state.update_data(phone=validated_phone)
        await message.answer("Выберите тип недвижимости:", reply_markup=get_property_type_keyboard())
        await state.set_state(RequestStates.property_type)
    except ValidationError as e:
        logger.error(f"Ошибка валидации телефона: {str(e)}")
        await message.answer(f"⚠️ {str(e)}! Введите в формате +7 XXX XXX XX XX, например, +7 999 123 45 67.\n"
                             "Рекомендации:\n- Номер должен начинаться с +7, 8 или 7.\n- Убедитесь, что номер содержит 11 цифр после +7 или 10 цифр после 8.\n"
                             "Попробуйте снова или отправьте контакт через кнопку ниже.",
                             reply_markup=ReplyKeyboardBuilder().add(KeyboardButton(text="📱 Отправить контакт", request_contact=True)).adjust(1).as_markup(
                                 resize_keyboard=True, input_field_placeholder="Введите в формате +7 XXX XXX XX XX"))
    except Exception as e:
        logger.error(f"Неожиданная ошибка валидации телефона: {str(e)}")
        await message.answer("⚠️ Произошла ошибка при обработке номера. Попробуйте снова или свяжитесь с поддержкой.")

# Обработчик выбора типа недвижимости (callback)
@router.callback_query(F.data.startswith("property_type_"), StateFilter(RequestStates.property_type))
async def process_property_type(callback: CallbackQuery, state: FSMContext):
    property_type = callback.data.replace("property_type_", "")
    await state.update_data(property_type=property_type)
    logger.info(f"ID: {callback.from_user.id} (@{callback.from_user.username}) - Выбор типа недвижимости: {property_type}")
    await callback.message.edit_text("Выберите тип сделки:", reply_markup=get_deal_type_keyboard())
    await state.set_state(RequestStates.deal_type)
    await callback.answer()

# Обработчик выбора типа сделки (callback)
@router.callback_query(F.data.startswith("deal_type_"), StateFilter(RequestStates.deal_type))
async def process_deal_type(callback: CallbackQuery, state: FSMContext):
    deal_type = callback.data.replace("deal_type_", "")
    await state.update_data(deal_type=deal_type)
    logger.info(f"ID: {callback.from_user.id} (@{callback.from_user.username}) - Выбор типа сделки: {deal_type}")
    await callback.message.edit_text("Выберите район:", reply_markup=get_district_keyboard())
    await state.set_state(RequestStates.district)
    await callback.answer()

# Обработчик выбора района (callback)
@router.callback_query(F.data.startswith("val_district_"), StateFilter(RequestStates.district))
async def process_district(callback: CallbackQuery, state: FSMContext):
    district = callback.data.replace("val_district_", "")
    await state.update_data(district=district)
    logger.info(f"ID: {callback.from_user.id} (@{callback.from_user.username}) - Выбор района: {district}")
    await callback.message.edit_text("Выберите бюджет:", reply_markup=get_budget_keyboard())
    await state.set_state(RequestStates.budget)
    await callback.answer()

# Обработчик выбора бюджета (callback)
@router.callback_query(F.data.startswith("budget_"), StateFilter(RequestStates.budget))
async def process_budget(callback: CallbackQuery, state: FSMContext):
    budget_str = callback.data.replace("budget_", "")
    budget_max = int(budget_str.split("-")[1]) if "-" in budget_str else int(budget_str)
    await state.update_data(budget=budget_max)
    logger.info(f"ID: {callback.from_user.id} (@{callback.from_user.username}) - Выбор бюджета: {budget_max}")
    await callback.message.edit_text("Выберите количество комнат:", reply_markup=get_rooms_keyboard())
    await state.set_state(RequestStates.rooms)
    await callback.answer()

# Обработчик выбора количества комнат (callback)
@router.callback_query(F.data.startswith("rooms_"), StateFilter(RequestStates.rooms))
async def process_rooms(callback: CallbackQuery, state: FSMContext):
    rooms_data = callback.data.replace("rooms_", "")
    if rooms_data.lower() == "none":
        rooms = None  # Устанавливаем None для "не важно"
    else:
        rooms = int(rooms_data)  # Преобразуем в число, если это не "не важно"
    await state.update_data(rooms=rooms)
    logger.info(f"ID: {callback.from_user.id} (@{callback.from_user.username}) - Выбор количества комнат: {rooms_data}")
    data = await state.get_data()
    search_criteria = {
        "property_type": data.get("property_type"),
        "deal_type": data.get("deal_type"),
        "district": data.get("district"),
        "budget": str(data.get("budget")),
        "rooms": rooms  # Передаем None или конкретное число
    }
    listings = await ListingService.get_filtered_listings(search_criteria)
    if listings:
        await state.update_data(filtered_listings=listings, selected_properties=[])
        for i, listing in enumerate(listings):
            text = f"🆔 ID: {listing.get('id', 'Не указан')}\n"
            address = listing.get('address', 'Адрес не указан')
            logger.info(f"Нормализованные данные объекта: {listing}")
            text += f"🏠 Адрес: {address if address.strip() else 'Адрес не указан'}\n"
            if listing.get('description'):
                text += f"📝 Описание: {listing.get('description', 'Описание не указано')}\n"
            if listing.get('floor'):
                text += f"🏢 Этаж: {listing.get('floor', 'Не указан')}\n"
            area = listing.get('area', 'Не указана')
            if area.lower() in ['нет', 'не указана'] or not area.replace('.', '').replace('м²', '').strip().isdigit():
                match = re.search(r'([0-9]+(?:[.,][0-9]+)?)\s?м²', listing.get('description', ''))
                area = f"{match.group(1).replace(',', '.') if match else 'Не указана'} м²"
                logger.debug(f"Извлечённая площадь из описания: {area}")
            else:
                area = f"{area} м²"
                logger.debug(f"Площадь из поля area: {area}")
            text += f"🏢 Площадь: {area}\n"
            if listing.get('contact_info'):
                text += f"📞 Контактная информация: {listing.get('contact_info', 'Не указаны')}\n"
            photo_urls = ListingService.get_property_photos(listing)
            if photo_urls:
                for j, url in enumerate(photo_urls):
                    try:
                        logger.info(f"Попытка отправки фото: {url}")
                        await callback.message.answer_photo(photo=url, caption=text if j == 0 else None)
                    except Exception as e:
                        logger.error(f"Ошибка при отправке фото {url}: {e}")
                        await callback.message.answer("⚠️ Не удалось загрузить одно из фото.")
            else:
                await callback.message.answer(text)
            keyboard = get_listing_menu(
                listing_exists=True,
                comments_provided=False,
                has_next_listing=(i < len(listings) - 1),
                listing_index=i,
                photo_index=0,
                total_photos=len(photo_urls),
                total_listings=len(listings),
                listing_id=listing.get('id')
            )
            await callback.message.answer("Выберите действие:", reply_markup=keyboard)
        await state.set_state(RequestStates.select_property)
    else:
        await callback.message.edit_text("Объекты не найдены. Завершение заявки.", reply_markup=None)
        await complete_request(callback.message, state)
    await callback.answer()

# Обработчик выбора объекта (callback)
@router.callback_query(F.data.startswith("request_"), StateFilter(RequestStates.select_property))
async def process_select_property(callback: CallbackQuery, state: FSMContext):
    property_id = int(callback.data.replace("request_", ""))
    data = await state.get_data()
    filtered_listings = data.get("filtered_listings", [])
    selected_properties = data.get("selected_properties", [])
    selected_property = next((l for l in filtered_listings if str(l.get('id')) == str(property_id)), None)
    if selected_property:
        if str(property_id) not in [p.get('id') for p in selected_properties]:
            selected_properties.append(selected_property)
            await state.update_data(selected_properties=selected_properties)
            logger.info(f"ID: {callback.from_user.id} (@{callback.from_user.username}) - Добавлен объект с ID: {property_id}")
        else:
            logger.info(f"ID: {callback.from_user.id} (@{callback.from_user.username}) - Объект с ID: {property_id} уже выбран")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Добавить ещё объект", callback_data="add_more")],
            [InlineKeyboardButton(text="Завершить и отправить заявку", callback_data="complete")]
        ])
        await callback.message.edit_text(f"Объект с ID {property_id} выбран. Выбрано объектов: {len(selected_properties)}\nВыберите действие:", reply_markup=keyboard)
    else:
        await callback.answer("Ошибка выбора объекта. Попробуйте снова.", show_alert=True)
    await callback.answer()

# Обработчик добавления ещё объекта или завершения
@router.callback_query(F.data.in_(["add_more", "complete"]), StateFilter(RequestStates.select_property))
async def process_selection_action(callback: CallbackQuery, state: FSMContext):
    if callback.data == "add_more":
        await callback.message.edit_text("Выберите следующий объект из списка.", reply_markup=None)
    elif callback.data == "complete":
        data = await state.get_data()
        selected_properties = data.get("selected_properties", [])
        if not selected_properties:
            await callback.message.edit_text("Вы не выбрали ни одного объекта. Завершение отменено.", reply_markup=None)
            await state.clear()
            return
        await state.update_data(selected_properties=selected_properties)
        await callback.message.edit_text("Введите комментарии к заявке (или нажмите /skip):")
        await state.set_state(RequestStates.comments)
    await callback.answer()

# Обработчик завершения заявки
@router.message(StateFilter(RequestStates.comments))
async def complete_request(message: Message, state: FSMContext):
    data = await state.get_data()
    comments = message.text.strip() if message.text != "/skip" else "Без комментариев"
    await state.update_data(comments=comments)
    selected_properties = data.get("selected_properties", [])
    # Преобразуем время в формат Moscow (UTC+3)
    moscow_offset = timedelta(hours=3)
    moscow_time = (message.date.replace(tzinfo=timezone.utc) + moscow_offset).strftime("%d-%m-%Y %H:%M")
    for i, prop in enumerate(selected_properties):
        request_data = {
            "timestamp": moscow_time,
            "user_id": message.from_user.id,
            "username": message.from_user.username or "Не указан",
            "user_name": data.get("name", "Не указан"),
            "phone": data.get("phone", "Не указан"),
            "property_id": prop.get("id", "N/A"),
            "property_address": prop.get("address", "Не указан"),
            "comments": comments
        }
        try:
            await google_sheets_service.save_request(request_data)
            logger.info(f"Заявка для объекта ID {prop.get('id')} успешно сохранена")
        except Exception as e:
            logger.error(f"Ошибка при сохранении заявки для объекта ID {prop.get('id')}: {str(e)}")
            await message.answer(f"⚠️ Ошибка при сохранении заявки для объекта ID {prop.get('id')}. Попробуйте позже.")
            await state.clear()
            return
    await message.answer("Все заявки успешно отправлены! Наши менеджеры свяжутся с вами в ближайшее время.", reply_markup=None)
    await state.clear()