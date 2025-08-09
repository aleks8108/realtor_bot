from aiogram import Router, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from services.gspread_utils import get_listings
from utils.keyboards import get_main_menu, get_property_type_keyboard, get_deal_type_keyboard, get_district_keyboard, get_budget_keyboard, get_rooms_keyboard, get_listing_menu
from aiogram import types
import logging
from config import ADMIN_ID
from handlers.request import RequestStates  # Импорт состояний для заявок

logging.basicConfig(level=logging.DEBUG)
router = Router()

class SearchStates(StatesGroup):
    awaiting_property_type = State()
    awaiting_deal_type = State()
    awaiting_district = State()
    awaiting_budget = State()
    awaiting_rooms = State()
    viewing_listings = State()

@router.callback_query(lambda c: c.data == "search")
async def start_search(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Запуск поиска недвижимости для пользователя {callback.from_user.id}")
    try:
        await callback.message.edit_text(
            "Начинаем поиск недвижимости. Выберите тип недвижимости:", 
            reply_markup=get_property_type_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            await callback.message.answer(
                "Начинаем поиск недвижимости. Выберите тип недвижимости:", 
                reply_markup=get_property_type_keyboard()
            )
    await state.set_state(SearchStates.awaiting_property_type)
    await callback.answer()

@router.callback_query(F.data.startswith("property_type_"))
async def process_property_type_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(property_type=callback.data.replace("property_type_", ""))
    try:
        await callback.message.edit_text(
            "Выберите тип сделки:", 
            reply_markup=get_deal_type_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            await callback.message.answer(
                "Выберите тип сделки:", 
                reply_markup=get_deal_type_keyboard()
            )
    await state.set_state(SearchStates.awaiting_deal_type)
    await callback.answer()

@router.callback_query(F.data.startswith("deal_type_"))
async def process_deal_type_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(deal_type=callback.data.replace("deal_type_", ""))
    try:
        await callback.message.edit_text(
            "Выберите район:", 
            reply_markup=get_district_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            await callback.message.answer(
                "Выберите район:", 
                reply_markup=get_district_keyboard()
            )
    await state.set_state(SearchStates.awaiting_district)
    await callback.answer()

@router.callback_query(F.data.startswith("district_"))
async def process_district_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(district=callback.data.replace("district_", ""))
    try:
        await callback.message.edit_text(
            "Выберите бюджет:", 
            reply_markup=get_budget_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            await callback.message.answer(
                "Выберите бюджет:", 
                reply_markup=get_budget_keyboard()
            )
    await state.set_state(SearchStates.awaiting_budget)
    await callback.answer()

@router.callback_query(F.data.startswith("budget_"))
async def process_budget_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(budget=callback.data.replace("budget_", ""))
    try:
        await callback.message.edit_text(
            "Выберите количество комнат:", 
            reply_markup=get_rooms_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            await callback.message.answer(
                "Выберите количество комнат:", 
                reply_markup=get_rooms_keyboard()
            )
    await state.set_state(SearchStates.awaiting_rooms)
    await callback.answer()

@router.callback_query(F.data.startswith("rooms_"))
async def process_rooms_callback(callback: CallbackQuery, state: FSMContext):
    rooms = callback.data.split('_')[1] if callback.data.startswith('rooms_') else None
    await state.update_data(rooms=rooms)
    data = await state.get_data()
    
    try:
        listings = get_listings()
    except Exception as e:
        logging.error(f"Ошибка при получении данных из Google Sheets: {e}")
        listings = []

    filtered_listings = [
        l for l in listings
        if l.get('property_type') == data['property_type'] and
           l.get('deal_type') == data['deal_type'] and
           l.get('district') == data['district'] and
           float(l.get('price', 0)) <= float(data['budget'].split('-')[-1]) and
           (rooms is None or str(l.get('rooms', '')) == str(rooms))
    ]

    await state.update_data(filtered_listings=filtered_listings, current_listing_index=0, current_photo_index=0)
    
    try:
        await callback.message.delete()
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения: {e}")

    if filtered_listings:
        await show_listing(callback.message, state)
    else:
        await callback.message.answer(
            "По вашим критериям ничего не найдено. Попробуйте изменить параметры поиска.",
            reply_markup=get_main_menu()
        )
        await state.clear()
    await callback.answer()

async def show_listing(message: types.Message, state: FSMContext):
    """
    Отправляет пользователю информацию о текущем объекте недвижимости и его фотографии.

    :param message: Объект сообщения aiogram.types.Message, в который будет отправлен ответ.
    :param state: Контекст состояния FSMContext для хранения и получения данных поиска.
    """
    data = await state.get_data()
    filtered_listings = data.get('filtered_listings', [])
    if not filtered_listings:
        await message.answer("Объекты не найдены.", reply_markup=get_main_menu())
        return

    current_listing_index = data.get('current_listing_index', 0)
    listing = filtered_listings[current_listing_index]
    photo_urls = (
        [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
        if isinstance(listing.get('photo_url'), str) else
        [url.strip() for url in listing.get('photo_url', []) if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
    )
    current_photo_index = data.get('current_photo_index', 0)
    logging.debug(f"show_listing: listing_index={current_listing_index}, photo_index={current_photo_index}, total_photos={len(photo_urls)}, listing={listing}")
    keyboard = get_listing_menu(
        listing_exists=True,
        comments_provided=False,
        has_next_listing=current_listing_index < len(filtered_listings) - 1,
        listing_index=current_listing_index,
        photo_index=current_photo_index,
        total_photos=len(photo_urls),
        total_listings=len(filtered_listings),
        listing_id=listing['id']
    )
    message_text = f"Объект {current_listing_index + 1}/{len(filtered_listings)}\nID: {listing['id']}\n{listing.get('description', 'Нет описания')}\nЦена: {listing['price']} ₽"
    await message.answer(message_text, reply_markup=keyboard)
    if photo_urls:
        await message.answer_photo(photo=photo_urls[current_photo_index])
    await state.set_state(SearchStates.viewing_listings)
    logging.info(f"Showing listing: index={current_listing_index}, total={len(filtered_listings)}")

@router.callback_query(F.data.startswith("next_photo_"))
async def next_photo_search(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    filtered_listings = data.get('filtered_listings', [])
    if not filtered_listings:
        await callback.answer("Нет доступных объектов.")
        return
    
    current_index = data.get('current_listing_index', 0)
    listing = filtered_listings[current_index]
    photo_urls = (
        [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip() and url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
        if isinstance(listing.get('photo_url'), str) else
        [url.strip() for url in listing.get('photo_url', []) if url.strip() and url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
    )
    
    callback_parts = callback.data.split('_')
    if len(callback_parts) != 4:
        await callback.answer("Неверный формат команды.")
        return
    new_listing_index = int(callback_parts[2])
    new_photo_index = int(callback_parts[3])
    
    if new_photo_index >= len(photo_urls):
        await callback.answer("Больше нет фотографий.")
        return
    
    await state.update_data(current_listing_index=new_listing_index, current_photo_index=new_photo_index)
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=photo_urls[new_photo_index],
        caption=f"Объект {new_listing_index + 1}/{len(filtered_listings)}\nID: {listing['id']}\n{listing['description']}\nЦена: {listing['price']} ₽\nФото {new_photo_index + 1}/{len(photo_urls)}",
        reply_markup=get_listing_menu(
            listing_exists=True,
            comments_provided=False,
            has_next_listing=new_listing_index < len(filtered_listings) - 1,
            listing_index=new_listing_index,
            photo_index=new_photo_index,
            total_photos=len(photo_urls),
            total_listings=len(filtered_listings),
            listing_id=listing['id']
        )
    )
    logging.info(f"Отправлено фото {new_photo_index + 1} для объекта ID {listing['id']} пользователю {callback.from_user.id}")
    await callback.answer()

@router.callback_query(F.data.startswith("prev_photo_"))
async def prev_photo_search(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    filtered_listings = data.get('filtered_listings', [])
    if not filtered_listings:
        await callback.answer("Нет доступных объектов.")
        return
    
    current_index = data.get('current_listing_index', 0)
    listing = filtered_listings[current_index]
    photo_urls = (
        [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip() and url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
        if isinstance(listing.get('photo_url'), str) else
        [url.strip() for url in listing.get('photo_url', []) if url.strip() and url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
    )
    
    callback_parts = callback.data.split('_')
    if len(callback_parts) != 4:
        await callback.answer("Неверный формат команды.")
        return
    new_listing_index = int(callback_parts[2])
    new_photo_index = int(callback_parts[3])
    
    if new_photo_index < 0:
        await callback.answer("Это первое фото.")
        return
    
    await state.update_data(current_listing_index=new_listing_index, current_photo_index=new_photo_index)
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=photo_urls[new_photo_index],
        caption=f"Объект {new_listing_index + 1}/{len(filtered_listings)}\nID: {listing['id']}\n{listing['description']}\nЦена: {listing['price']} ₽\nФото {new_photo_index + 1}/{len(photo_urls)}",
        reply_markup=get_listing_menu(
            listing_exists=True,
            comments_provided=False,
            has_next_listing=new_listing_index < len(filtered_listings) - 1,
            listing_index=new_listing_index,
            photo_index=new_photo_index,
            total_photos=len(photo_urls),
            total_listings=len(filtered_listings),
            listing_id=listing['id']
        )
    )
    logging.info(f"Отправлено фото {new_photo_index + 1} для объекта ID {listing['id']} пользователю {callback.from_user.id}")
    await callback.answer()

@router.callback_query(F.data.startswith("next_listing_"))
async def next_listing_search(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    filtered_listings = data.get('filtered_listings', [])
    if not filtered_listings:
        await callback.answer("Нет доступных объектов.")
        return
    
    callback_parts = callback.data.split('_')
    if len(callback_parts) != 3:
        await callback.answer("Неверный формат команды.")
        return
    new_listing_index = int(callback_parts[2])
    
    if new_listing_index >= len(filtered_listings):
        await callback.answer("Больше нет объектов.")
        return
    
    listing = filtered_listings[new_listing_index]
    photo_urls = [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
    await state.update_data(current_listing_index=new_listing_index, current_photo_index=0)
    
    await callback.message.delete()
    message_text = f"Объект {new_listing_index + 1}/{len(filtered_listings)}\nID: {listing['id']}\n{listing['description']}\nЦена: {listing['price']} ₽"
    keyboard = get_listing_menu(
        listing_exists=True,
        comments_provided=False,
        has_next_listing=new_listing_index < len(filtered_listings) - 1,
        listing_index=new_listing_index,
        photo_index=0,
        total_photos=len(photo_urls),
        total_listings=len(filtered_listings),
        listing_id=listing['id']
    )
    await callback.message.answer(message_text, reply_markup=keyboard)
    if photo_urls:
        await callback.message.answer_photo(photo=photo_urls[0])
    logging.info(f"Отправлен объект {new_listing_index + 1} (ID: {listing['id']}) пользователю {callback.from_user.id}")
    await callback.answer()

@router.callback_query(F.data.startswith("prev_listing_"))
async def prev_listing_search(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    filtered_listings = data.get('filtered_listings', [])
    if not filtered_listings:
        await callback.answer("Нет доступных объектов.")
        return
    
    callback_parts = callback.data.split('_')
    if len(callback_parts) != 3:
        await callback.answer("Неверный формат команды.")
        return
    new_listing_index = int(callback_parts[2])
    
    if new_listing_index < 0:
        await callback.answer("Это первый объект.")
        return
    
    listing = filtered_listings[new_listing_index]
    photo_urls = [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
    await state.update_data(current_listing_index=new_listing_index, current_photo_index=0)
    
    await callback.message.delete()
    message_text = f"Объект {new_listing_index + 1}/{len(filtered_listings)}\nID: {listing['id']}\n{listing['description']}\nЦена: {listing['price']} ₽"
    keyboard = get_listing_menu(
        listing_exists=True,
        comments_provided=False,
        has_next_listing=new_listing_index < len(filtered_listings) - 1,
        listing_index=new_listing_index,
        photo_index=0,
        total_photos=len(photo_urls),
        total_listings=len(filtered_listings),
        listing_id=listing['id']
    )
    await callback.message.answer(message_text, reply_markup=keyboard)
    if photo_urls:
        await callback.message.answer_photo(photo=photo_urls[0])
    logging.info(f"Отправлен объект {new_listing_index + 1} (ID: {listing['id']}) пользователю {callback.from_user.id}")
    await callback.answer()

@router.callback_query(F.data.startswith("interested_"))
async def interested(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает интерес к объекту, отправляет уведомление админу и запрашивает комментарий.
    """
    listing_id = callback.data.replace("interested_", "")
    data = await state.get_data()
    filtered_listings = data.get('filtered_listings', [])
    listing = next((l for l in filtered_listings if str(l['id']) == listing_id), None)
    
    if not listing:
        await callback.answer("Объект не найден.")
        return
    
    # Уведомление админу
    if ADMIN_ID:
        await callback.bot.send_message(
            ADMIN_ID[0],
            f"Пользователь {callback.from_user.id} (@{callback.from_user.username or 'no_username'}) заинтересован в объекте ID: {listing_id}\n"
            f"{listing.get('description', 'Нет описания')}\nЦена: {listing.get('price', 'Не указана')} ₽"
        )
    
    # Запрос комментария
    current_listing_index = data.get('current_listing_index', 0)
    listing = filtered_listings[current_listing_index]
    photo_urls = (
        [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
        if isinstance(listing.get('photo_url'), str) else
        [url.strip() for url in listing.get('photo_url', []) if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
    )
    message_text = f"Ваш интерес к объекту ID: {listing_id} зафиксирован.\n\nПожалуйста, введите комментарий к заявке (или напишите 'Без комментариев'):"
    keyboard = get_listing_menu(
        listing_exists=True,
        comments_provided=False,
        has_next_listing=current_listing_index < len(filtered_listings) - 1,
        listing_index=current_listing_index,
        photo_index=data.get('current_photo_index', 0),
        total_photos=len(photo_urls),
        total_listings=len(filtered_listings),
        listing_id=listing['id']
    )
    await callback.message.answer(message_text, reply_markup=keyboard)
    if photo_urls:
        await callback.message.answer_photo(photo=photo_urls[data.get('current_photo_index', 0)])
    await state.set_state(RequestStates.comments)  # Переход к состоянию ввода комментария
    await callback.answer("Ваш интерес зафиксирован. Пожалуйста, введите комментарий.")
    logging.info(f"Пользователь {callback.from_user.id} заинтересован в объекте ID: {listing_id}")