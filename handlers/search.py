
#____________________________________________________________________________________________________#

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.methods import SendMediaGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from services.gspread_utils import get_listings
from keyboards.main_menu import get_main_menu
import logging
import asyncio
from requests.exceptions import SSLError
import gspread
from google.oauth2.service_account import Credentials
import json
import csv
import os

router = Router()

class SearchStates(StatesGroup):
    awaiting_property_type = State()
    awaiting_deal_type = State()
    awaiting_district = State()
    awaiting_budget = State()
    awaiting_rooms = State()
    viewing_listings = State()

# Аутентификация и создание клиента gspread
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_file('credentials.json', scopes=scopes)
gc = gspread.Client(auth=credentials)

# Кэш для данных
_cache = {}
_cache_timeout = 300  # 5 минут

async def cached_get_listings():
    global _cache
    try:
        loop = asyncio.get_event_loop()
        current_time = loop.time()
        if _cache and (current_time - _cache.get('timestamp', 0)) < _cache_timeout:
            logging.info("Using cached data from Google Sheets or CSV...")
            return _cache['data']
        logging.info("Attempting to fetch data from Google Sheets...")
        listings = await loop.run_in_executor(None, lambda: gc.open_by_key("1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w").worksheet("listings").get_all_records())
        # Логируем декодированные значения
        for listing in listings:
            for key, value in listing.items():
                if isinstance(value, str):
                    logging.info(f"Decoded data for {key}: {value}")
        logging.info("Data fetch completed, processing records...")
        logging.info(f"Successfully fetched {len(listings)} records from Google Sheets: {listings[:2]}...")
        _cache = {'data': listings, 'timestamp': current_time}
        return listings
    except SSLError as e:
        logging.error(f"Ошибка SSL при подключении к Google Sheets: {e}")
        return _cache.get('data', []) if _cache else []
    except Exception as e:
        logging.error(f"Ошибка при получении данных из Google Sheets: {e}")
        csv_path = "карточка объекта - listings.csv"
        if os.path.exists(csv_path):
            logging.info(f"Попытка загрузки данных из CSV: {csv_path}")
            listings = []
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    row['price'] = float(row['price'].replace(',', '.'))
                    listings.append(row)
            logging.info(f"Successfully fetched {len(listings)} records from CSV: {listings[:2]}...")
            _cache = {'data': listings, 'timestamp': current_time}
            return listings
        return _cache.get('data', []) if _cache else []

@router.callback_query(lambda c: c.data == "search")
async def start_search(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Квартира", callback_data="property_type_Квартира"),
         InlineKeyboardButton(text="Дом", callback_data="property_type_Дом")],
        [InlineKeyboardButton(text="Коммерческая", callback_data="property_type_Коммерческая"),
         InlineKeyboardButton(text="Земельный участок", callback_data="property_type_Земельный участок")]
    ])
    await callback.message.edit_text("Начинаем поиск недвижимости. Выберите тип недвижимости:", reply_markup=keyboard)
    await state.set_state(SearchStates.awaiting_property_type)
    await callback.answer()

@router.callback_query(F.data.startswith("property_type_"))
async def process_property_type_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(property_type=callback.data.replace("property_type_", ""))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Покупка", callback_data="deal_type_Покупка"),
         InlineKeyboardButton(text="Аренда", callback_data="deal_type_Аренда")]
    ])
    await callback.message.edit_text("Выберите тип сделки:", reply_markup=keyboard)
    await state.set_state(SearchStates.awaiting_deal_type)
    await callback.answer()

@router.callback_query(F.data.startswith("deal_type_"))
async def process_deal_type_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(deal_type=callback.data.replace("deal_type_", ""))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Центральный", callback_data="district_Центральный"),
         InlineKeyboardButton(text="Западный", callback_data="district_Западный")],
        [InlineKeyboardButton(text="Прикубанский", callback_data="district_Прикубанский"),
         InlineKeyboardButton(text="Карасунский", callback_data="district_Карасунский")]
    ])
    await callback.message.edit_text("Выберите район:", reply_markup=keyboard)
    await state.set_state(SearchStates.awaiting_district)
    await callback.answer()

@router.callback_query(F.data.startswith("district_"))
async def process_district_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(district=callback.data.replace("district_", ""))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="0-5 млн", callback_data="budget_0-5000000"),
         InlineKeyboardButton(text="5-10 млн", callback_data="budget_5000000-10000000"),
         InlineKeyboardButton(text="10-50 млн", callback_data="budget_10000000-50000000"),  # Увеличим верхнюю границу
         InlineKeyboardButton(text="50-100 млн", callback_data="budget_50000000-100000000")]
    ])
    await callback.message.edit_text("Выберите бюджет:", reply_markup=keyboard)
    await state.set_state(SearchStates.awaiting_budget)
    await callback.answer()

@router.callback_query(F.data.startswith("budget_"))
async def process_budget_callback(callback: CallbackQuery, state: FSMContext):
    budget_range = callback.data.replace("budget_", "").split("-")
    await state.update_data(budget=budget_range[1])  # Используем верхнюю границу
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 комната", callback_data="rooms_1"),
         InlineKeyboardButton(text="2 комнаты", callback_data="rooms_2"),
         InlineKeyboardButton(text="3 комнаты", callback_data="rooms_3")],
        [InlineKeyboardButton(text="4 комнаты", callback_data="rooms_4"),
         InlineKeyboardButton(text="5 комнат", callback_data="rooms_5"),
         InlineKeyboardButton(text="Не выбрано", callback_data="rooms_none")]
    ])
    await callback.message.edit_text("Выберите количество комнат:", reply_markup=keyboard)
    await state.set_state(SearchStates.awaiting_rooms)
    await callback.answer()

@router.callback_query(F.data.startswith("rooms_"))
async def process_rooms_callback(callback: CallbackQuery, state: FSMContext):
    rooms = callback.data.replace("rooms_", "") if callback.data != "rooms_none" else None
    await state.update_data(rooms=rooms)
    try:
        await perform_search(callback.message, state)
    except TelegramBadRequest as e:
        logging.warning(f"Пропуск устаревшего запроса: {e}")
    await callback.answer()

async def perform_search(message: Message, state: FSMContext):
    data = await state.get_data()
    logging.info(f"Поиск с фильтрами: {data}")
    listings = await cached_get_listings()
    logging.info(f"Полученные данные из cached_get_listings: {listings}...")

    # Добавляем отладку сырых данных для всех листингов
    logging.info(f"Raw filter values - property_type: {data.get('property_type')}, deal_type: {data.get('deal_type')}, "
                 f"district: {data.get('district')}, budget: {data.get('budget')}, rooms: {data.get('rooms')}")
    for listing in listings:
        logging.info(f"Raw listing data: {listing}")

    filtered_listings = []
    for l in listings:
        try:
            price = float(str(l.get("price", "0")).replace(",", ".").replace(" ", ""))
            budget = float(data.get("budget", "0")) if data.get("budget") else None
            logging.info(f"Converted - price: {price}, budget: {budget}")
            
            matches_property = not data.get("property_type") or l.get("property_type", "").lower() == data.get("property_type").lower()
            matches_deal = not data.get("deal_type") or l.get("deal_type", "").lower() == data.get("deal_type").lower()
            matches_district = not data.get("district") or l.get("district", "").lower() == data.get("district").lower()
            matches_rooms = not data.get("rooms") or str(l.get("rooms", "0")) == str(data.get("rooms"))
            matches_budget = not budget or price <= budget

            if matches_property and matches_deal and matches_district and matches_rooms and matches_budget:
                filtered_listings.append(l)
        except ValueError as e:
            logging.error(f"Ошибка преобразования в float: {e}, listing: {l}, budget: {data.get('budget')}")
            continue

    logging.info(f"Filtered listings count: {len(filtered_listings)}, first item: {filtered_listings[:1] if filtered_listings else 'None'}")
    if not filtered_listings:
        await message.answer("К сожалению, подходящих объектов не найдено или произошла ошибка подключения к данным.", reply_markup=get_main_menu())
        await state.clear()
        return

    await state.update_data(filtered_listings=filtered_listings, current_listing_index=0, current_photo_index=0)
    await state.set_state(SearchStates.viewing_listings)
    await show_listing(message, state)

async def show_listing(message: Message, state: FSMContext):
    data = await state.get_data()
    filtered_listings = data.get("filtered_listings", [])
    current_listing_index = data.get("current_listing_index", 0)
    current_photo_index = data.get("current_photo_index", 0)

    logging.info(f"Showing listing: index={current_listing_index}, total={len(filtered_listings)}")
    if not filtered_listings or current_listing_index < 0 or current_listing_index >= len(filtered_listings):
        logging.error(f"Недопустимый индекс объекта: {current_listing_index}, длина списка: {len(filtered_listings)}")
        await message.answer("Ошибка при отображении объекта.", reply_markup=get_main_menu())
        await state.clear()
        return

    listing = filtered_listings[current_listing_index]
    photo_urls = (
        [url.strip() for url in listing.get("photo_url", "").split(",") if url.strip().startswith("http") and url.strip().endswith((".jpg", ".jpeg", ".png"))]
        if isinstance(listing.get("photo_url"), str) else
        listing.get("photo_url", [])
    )
    photo_urls = [url for url in photo_urls if url]

    if not photo_urls:
        logging.warning(f"Нет валидных фотографий для объекта ID: {listing['id']}")
        await message.answer(f"Объект {current_listing_index + 1}/{len(filtered_listings)}\nID: {listing['id']}\n{listing.get('description', 'Нет описания')}\n(Нет фотографий)", reply_markup=get_main_menu())
        await state.clear()
        return

    current_photo = photo_urls[current_photo_index]

    inline_buttons = [
        [InlineKeyboardButton(text="Интересует", callback_data=f"interested_{listing['id']}")]
    ]
    if current_photo_index > 0:
        inline_buttons.append([InlineKeyboardButton(text="⬅️ Пред. фото", callback_data=f"prev_photo_{current_listing_index}_{current_photo_index-1}")])
    if current_photo_index < len(photo_urls) - 1:
        inline_buttons.append([InlineKeyboardButton(text="След. фото ➡️", callback_data=f"next_photo_{current_listing_index}_{current_photo_index+1}")])
    if current_listing_index > 0:
        inline_buttons.append([InlineKeyboardButton(text="⬅️ Пред. объект", callback_data=f"prev_listing_{current_listing_index-1}_0")])
    if current_listing_index < len(filtered_listings) - 1:
        inline_buttons.append([InlineKeyboardButton(text="След. объект ➡️", callback_data=f"next_listing_{current_listing_index+1}_0")])
    inline_buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="return_to_menu")])
    inline_buttons.append([InlineKeyboardButton(text="🗑 Очистить чат", callback_data="clear_chat")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    try:
        await message.answer_photo(photo=current_photo)
        await message.answer(
            f"Объект {current_listing_index + 1}/{len(filtered_listings)}\nID: {listing['id']}\n{listing.get('description', 'Нет описания')}\nФото {current_photo_index + 1}/{len(photo_urls)}",
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке медиа для объекта ID: {listing['id']}: {e}")
        await message.answer(f"Ошибка при отображении фото для объекта ID: {listing['id']}\n{listing.get('description', 'Нет описания')}", reply_markup=keyboard)

@router.callback_query(F.data.startswith("next_photo_"))
async def process_next_photo(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Callback data: {callback.data}")
    listing_index, photo_index = map(int, callback.data.replace("next_photo_", "").split("_"))
    await state.update_data(current_listing_index=listing_index, current_photo_index=photo_index)
    await show_listing(callback.message, state)
    await callback.answer()

@router.callback_query(F.data.startswith("prev_photo_"))
async def process_prev_photo(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Callback data: {callback.data}")
    listing_index, photo_index = map(int, callback.data.replace("prev_photo_", "").split("_"))
    await state.update_data(current_listing_index=listing_index, current_photo_index=photo_index)
    await show_listing(callback.message, state)
    await callback.answer()

@router.callback_query(F.data.startswith("next_listing_"))
async def process_next_listing(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Callback data: {callback.data}")
    listing_index, photo_index = map(int, callback.data.replace("next_listing_", "").split("_"))
    await state.update_data(current_listing_index=listing_index, current_photo_index=photo_index)
    logging.info(f"Updated index to: {listing_index}")
    await show_listing(callback.message, state)
    await callback.answer()

@router.callback_query(F.data.startswith("prev_listing_"))
async def process_prev_listing(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Callback data: {callback.data}")
    listing_index, photo_index = map(int, callback.data.replace("prev_listing_", "").split("_"))
    await state.update_data(current_listing_index=listing_index, current_photo_index=photo_index)
    logging.info(f"Updated index to: {listing_index}")
    await show_listing(callback.message, state)
    await callback.answer()

@router.callback_query(F.data.startswith("interested_"))
async def process_interested(callback: CallbackQuery):
    listing_id = callback.data.replace("interested_", "")
    admin_id = 1623975688  # Замените на реальный ID администратора
    try:
        await callback.bot.send_message(
            chat_id=admin_id,
            text=f"Интерес к объекту ID: {listing_id} от {callback.from_user.username or callback.from_user.full_name}"
        )
        await callback.message.answer(f"Ваш интерес к объекту ID: {listing_id} отправлен администратору!")
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления администратору: {e}")
        await callback.message.answer("Произошла ошибка при отправке запроса администратору.")
    await callback.answer()

@router.callback_query(F.data == "clear_chat")
async def clear_chat(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения: {e}")
    await callback.answer("Чат очищен.")

@router.callback_query(F.data == "return_to_menu")
async def return_to_menu(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text("Вы вернулись в главное меню.\nВыберите действие:", reply_markup=get_main_menu())
        await state.clear()
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
    await callback.answer()
    
#___________________________________________________________________________________________#

""" from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.methods import SendMediaGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from services.gspread_utils import get_listings
from keyboards.main_menu import get_main_menu
import logging
import asyncio
from requests.exceptions import SSLError
import gspread
from google.oauth2.service_account import Credentials
import json
import csv
import os

router = Router()

class SearchStates(StatesGroup):
    awaiting_property_type = State()
    awaiting_deal_type = State()
    awaiting_district = State()
    awaiting_budget = State()
    awaiting_rooms = State()
    viewing_listings = State()

# Аутентификация и создание клиента gspread
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_file('credentials.json', scopes=scopes)
gc = gspread.Client(auth=credentials)

# Кэш для данных
_cache = {}
_cache_timeout = 300  # 5 минут

async def cached_get_listings():
    global _cache
    try:
        loop = asyncio.get_event_loop()
        current_time = loop.time()
        if _cache and (current_time - _cache.get('timestamp', 0)) < _cache_timeout:
            logging.info("Using cached data from Google Sheets or CSV...")
            return _cache['data']
        logging.info("Attempting to fetch data from Google Sheets...")
        listings = await loop.run_in_executor(None, lambda: gc.open_by_key("1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w").worksheet("listings").get_all_records())
        # Декодируем строки в UTF-8 с учётом возможной латинской кодировки
        for listing in listings:
            for key, value in listing.items():
                if isinstance(value, str):
                    try:
                        listing[key] = value.encode('latin1').decode('utf-8', errors='replace')
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        listing[key] = value  # Оставляем как есть, если декодирование не удалось
        logging.info("Data fetch completed, processing records...")
        logging.info(f"Successfully fetched {len(listings)} records from Google Sheets: {listings[:2]}...")
        _cache = {'data': listings, 'timestamp': current_time}
        return listings
    except SSLError as e:
        logging.error(f"Ошибка SSL при подключении к Google Sheets: {e}")
        return _cache.get('data', []) if _cache else []
    except Exception as e:
        logging.error(f"Ошибка при получении данных из Google Sheets: {e}")
        # Попытка загрузки из CSV как резервный вариант
        csv_path = "карточка объекта - listings.csv"
        if os.path.exists(csv_path):
            logging.info(f"Попытка загрузки данных из CSV: {csv_path}")
            listings = []
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Преобразуем price в число для фильтрации
                    row['price'] = float(row['price'].replace(',', '.'))
                    listings.append(row)
            logging.info(f"Successfully fetched {len(listings)} records from CSV: {listings[:2]}...")
            _cache = {'data': listings, 'timestamp': current_time}
            return listings
        return _cache.get('data', []) if _cache else []  """