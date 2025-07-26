from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from services.sheets import init_sheets
from config import ADMIN_ID
from keyboards.search_filters import get_property_type_keyboard, get_deal_type_keyboard, get_district_keyboard, get_budget_keyboard, get_start_reply_keyboard
import logging
import gspread
import asyncio
import time
import aiogram.exceptions

router = Router()

class SearchStates(StatesGroup):
    property_type = State()
    deal_type = State()
    district = State()
    budget = State()
    rooms = State()

# Кэш данных Google Sheets
_listings_cache = None
_cache_timestamp = 0
_CACHE_TTL = 300  # 5 минут

async def get_listings():
    global _listings_cache, _cache_timestamp
    if _listings_cache is None or time.time() - _cache_timestamp > _CACHE_TTL:
        try:
            sheet = init_sheets()
            _listings_cache = sheet.get_all_records()
            _cache_timestamp = time.time()
            logging.info(f"Обновлен кэш записей: {len(_listings_cache)}")
        except gspread.exceptions.APIError as e:
            logging.error(f"Ошибка API Google Sheets: {e}")
            _listings_cache = []
    return _listings_cache

@router.message(F.text == "🏠 Найти недвижимость")
async def start_search(message: types.Message, state: FSMContext):
    logging.info(f"Кнопка 'Найти недвижимость' нажата пользователем {message.from_user.id}, message_id={message.message_id}")
    await state.update_data(search_message_ids=[message.message_id])
    response = await message.answer("Выберите тип недвижимости:", reply_markup=get_property_type_keyboard())
    data = await state.get_data()
    search_message_ids = data.get("search_message_ids", [])
    if response.message_id not in search_message_ids:
        search_message_ids.append(response.message_id)
        logging.debug(f"Добавлен message_id={response.message_id} в start_search")
    await state.update_data(search_message_ids=search_message_ids)
    await state.set_state(SearchStates.property_type)

@router.callback_query(SearchStates.property_type)
async def process_property_type(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    search_message_ids = data.get("search_message_ids", [])
    if callback.message.message_id not in search_message_ids:
        search_message_ids.append(callback.message.message_id)
        logging.debug(f"Добавлен message_id={callback.message.message_id} в process_property_type")
    await state.update_data(search_message_ids=search_message_ids)
    await state.update_data(property_type=callback.data)
    await callback.message.edit_text("Выберите тип сделки:", reply_markup=get_deal_type_keyboard())
    await state.set_state(SearchStates.deal_type)
    await callback.answer()

@router.callback_query(SearchStates.deal_type)
async def process_deal_type(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    search_message_ids = data.get("search_message_ids", [])
    if callback.message.message_id not in search_message_ids:
        search_message_ids.append(callback.message.message_id)
        logging.debug(f"Добавлен message_id={callback.message.message_id} в process_deal_type")
    await state.update_data(search_message_ids=search_message_ids)
    await state.update_data(deal_type=callback.data)
    await callback.message.edit_text("Выберите район:", reply_markup=get_district_keyboard())
    await state.set_state(SearchStates.district)
    await callback.answer()

@router.callback_query(SearchStates.district)
async def process_district(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    search_message_ids = data.get("search_message_ids", [])
    if callback.message.message_id not in search_message_ids:
        search_message_ids.append(callback.message.message_id)
        logging.debug(f"Добавлен message_id={callback.message.message_id} в process_district")
    await state.update_data(search_message_ids=search_message_ids)
    await state.update_data(district=callback.data)
    await callback.message.edit_text("Выберите бюджет:", reply_markup=get_budget_keyboard())
    await state.set_state(SearchStates.budget)
    await callback.answer()

@router.callback_query(SearchStates.budget)
async def process_budget(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    search_message_ids = data.get("search_message_ids", [])
    if callback.message.message_id not in search_message_ids:
        search_message_ids.append(callback.message.message_id)
        logging.debug(f"Добавлен message_id={callback.message.message_id} в process_budget")
    await state.update_data(search_message_ids=search_message_ids)
    budget = callback.data
    await state.update_data(budget=budget)
    data = await state.get_data()
    if data["property_type"] in ["Квартира", "Коммерческая"]:
        await callback.message.edit_text("Введите количество комнат (например, 2) или пропустите, нажав Enter для 'Любое':")
        await state.set_state(SearchStates.rooms)
    else:
        await perform_search(callback.message, state)
    await callback.answer()

@router.message(SearchStates.rooms)
async def process_rooms(message: types.Message, state: FSMContext):
    data = await state.get_data()
    search_message_ids = data.get("search_message_ids", [])
    if message.message_id not in search_message_ids:
        search_message_ids.append(message.message_id)
        logging.debug(f"Добавлен message_id={message.message_id} в process_rooms")
    await state.update_data(search_message_ids=search_message_ids)
    rooms = message.text.strip() or "Любое"
    if rooms != "Любое" and not rooms.isdigit():
        response = await message.answer("Пожалуйста, введите число комнат (например, 2) или пропустите (Enter).")
        if response.message_id not in search_message_ids:
            search_message_ids.append(response.message_id)
            logging.debug(f"Добавлен message_id={response.message_id} в process_rooms (ошибка ввода)")
        await state.update_data(search_message_ids=search_message_ids)
        return
    await state.update_data(rooms=rooms)
    await perform_search(message, state)

async def perform_search(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        logging.info(f"Поиск с фильтрами: {data}")
        listings = await get_listings()
        logging.info(f"Получено записей из кэша: {len(listings)}")
        
        filtered_listings = []
        for listing in listings:
            if not is_valid_listing(listing, data):
                continue
            filtered_listings.append(listing)
        filtered_listings = filtered_listings[:5]
        
        if not filtered_listings:
            response = await message.answer("К сожалению, ничего не найдено. Попробуйте изменить фильтры.")
            search_message_ids = data.get("search_message_ids", [])
            if response.message_id not in search_message_ids:
                search_message_ids.append(response.message_id)
                logging.debug(f"Добавлен message_id={response.message_id} для 'ничего не найдено'")
            await state.update_data(search_message_ids=list(set(search_message_ids)))
            logging.info("Результаты поиска: ничего не найдено")
            await state.clear()
            return

        search_message_ids = data.get("search_message_ids", [])
        for listing in filtered_listings:
            text = (f"🏠 ID: {listing['id']} | {listing['property_type']} ({listing['deal_type']})\n"
                    f"📍 {listing['district']}\n"
                    f"💰 {listing['price']} руб.\n"
                    f"🛋 Комнат: {listing.get('rooms', 'Не указано')}\n"
                    f"📝 {listing.get('description', 'Нет описания')}")
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Интересует", callback_data=f"interested_{listing['id']}")]
            ])

            # Обработка фотографий
            photo_urls = listing.get("photo_urls") or ""
            if isinstance(photo_urls, str):
                photo_urls = photo_urls.strip()
            else:
                photo_urls = ""
            try:
                if photo_urls:
                    urls = [url.strip() for url in photo_urls.split(",") if url.strip()]
                    if urls:
                        # Отправка медиа-группы (по 10 фото)
                        for i in range(0, len(urls), 10):
                            chunk = urls[i:i+10]
                            media = [
                                InputMediaPhoto(media=url, caption=text if i == 0 and j == 0 else None)
                                for j, url in enumerate(chunk)
                            ]
                            media_message = await message.answer_media_group(media=media)
                            for msg in media_message:
                                if msg.message_id not in search_message_ids:
                                    search_message_ids.append(msg.message_id)
                            logging.debug(f"Отправлена медиа-группа для записи {listing['id']} с {len(chunk)} фото, message_ids={[m.message_id for m in media_message]}")
                        # Отправка текста с кнопкой
                        text_message = await message.answer(text, reply_markup=markup)
                        if text_message.message_id not in search_message_ids:
                            search_message_ids.append(text_message.message_id)
                        logging.debug(f"Отправлено текстовое сообщение с кнопкой для записи {listing['id']}, message_id={text_message.message_id}")
                    else:
                        # Отправка одной фотографии
                        photo_message = await message.answer_photo(
                            photo=urls[0],
                            caption=text,
                            reply_markup=markup
                        )
                        if photo_message.message_id not in search_message_ids:
                            search_message_ids.append(photo_message.message_id)
                        logging.debug(f"Отправлена одна фотография с кнопкой для записи {listing['id']}, message_id={photo_message.message_id}")
                else:
                    # Если нет фотографий
                    text_message = await message.answer(text, reply_markup=markup)
                    if text_message.message_id not in search_message_ids:
                        search_message_ids.append(text_message.message_id)
                    logging.debug(f"Отправлен текст с кнопкой для записи {listing['id']} без фотографий, message_id={text_message.message_id}")
            except Exception as e:
                logging.warning(f"Ошибка отправки для записи {listing['id']}: {e}")
                text_message = await message.answer(text, reply_markup=markup)
                if text_message.message_id not in search_message_ids:
                    search_message_ids.append(text_message.message_id)
                logging.debug(f"Отправлен текст с кнопкой для записи {listing['id']} после ошибки, message_id={text_message.message_id}")
        
        await state.update_data(search_message_ids=list(set(search_message_ids)))
        logging.debug(f"Сохранены message_ids: {search_message_ids}")
        logging.info(f"Отправлено {len(filtered_listings)} результатов поиска")
        await state.clear()
    except gspread.exceptions.GSpreadException as e:
        response = await message.answer(f"Ошибка в структуре таблицы: {str(e)}. Обратитесь к администратору.")
        search_message_ids = data.get("search_message_ids", [])
        if response.message_id not in search_message_ids:
            search_message_ids.append(response.message_id)
            logging.debug(f"Добавлен message_id={response.message_id} для ошибки GSpread")
        await state.update_data(search_message_ids=list(set(search_message_ids)))
        logging.error(f"Ошибка в структуре таблицы: {e}")
        await state.clear()
    except Exception as e:
        response = await message.answer(f"Произошла ошибка при поиске: {str(e)}")
        search_message_ids = data.get("search_message_ids", [])
        if response.message_id not in search_message_ids:
            search_message_ids.append(response.message_id)
            logging.debug(f"Добавлен message_id={response.message_id} для общей ошибки")
        await state.update_data(search_message_ids=list(set(search_message_ids)))
        logging.error(f"Ошибка при поиске: {e}")
        await state.clear()

def is_valid_listing(listing: dict, data: dict) -> bool:
    try:
        listing_property_type = str(listing.get("property_type", "")).strip()
        if listing_property_type != data["property_type"]:
            logging.debug(f"Запись {listing.get('id')} отклонена: property_type={listing_property_type} != {data['property_type']}")
            return False

        listing_deal_type = str(listing.get("deal_type", "")).strip()
        if listing_deal_type != data["deal_type"]:
            logging.debug(f"Запись {listing.get('id')} отклонена: deal_type={listing_deal_type} != {data['deal_type']}")
            return False

        listing_district = str(listing.get("district", "")).strip()
        if listing_district != data["district"]:
            logging.debug(f"Запись {listing.get('id')} отклонена: district={listing_district} != {data['district']}")
            return False

        price = listing.get("price", 0)
        if isinstance(price, str):
            if not price.strip().isdigit():
                logging.warning(f"Некорректная цена в записи {listing.get('id')}: {price}")
                return False
            price = int(price.strip())
        elif not isinstance(price, int):
            logging.warning(f"Некорректный тип цены в записи {listing.get('id')}: {type(price)}")
            return False
        if not is_in_budget(price, data["budget"]):
            logging.debug(f"Запись {listing.get('id')} отклонена: price={price} не в бюджете {data['budget']}")
            return False

        rooms = data.get("rooms", "Любое")
        listing_rooms = str(listing.get("rooms", "")).strip()
        if rooms != "Любое" and listing_rooms and listing_rooms != rooms:
            logging.debug(f"Запись {listing.get('id')} отклонена: rooms={listing_rooms} != {rooms}")
            return False
        if rooms != "Любое" and not listing_rooms:
            logging.debug(f"Запись {listing.get('id')} отклонена: rooms пустое, требуется {rooms}")
            return False

        logging.debug(f"Запись {listing.get('id')} прошла фильтры")
        return True
    except Exception as e:
        logging.warning(f"Ошибка при валидации записи {listing.get('id')}: {e}")
        return False

def is_in_budget(price: int, budget: str) -> bool:
    try:
        if not isinstance(budget, str) or "-" not in budget:
            logging.warning(f"Некорректный формат бюджета: {budget}")
            return False
        min_budget, max_budget = map(int, budget.split("-"))
        result = min_budget <= price <= max_budget
        logging.debug(f"Проверка бюджета: price={price}, budget={min_budget}-{max_budget}, результат={result}")
        return result
    except ValueError as e:
        logging.warning(f"Ошибка при проверке бюджета: price={price}, budget={budget}, ошибка={e}")
        return False

@router.callback_query(F.data.startswith("interested_"))
async def process_interested(callback: types.CallbackQuery, state: FSMContext):
    try:
        listing_id = callback.data.split("_")[1]
        logging.debug(f"Нажата кнопка 'Интересует' для записи {listing_id} пользователем {callback.from_user.id}")
        listings = await get_listings()
        listing = next((l for l in listings if str(l.get("id", "")) == listing_id), None)
        
        if listing:
            text = (f"Клиент заинтересован в объекте:\n"
                    f"🏠 ID: {listing['id']} | {listing['property_type']} ({listing['deal_type']})\n"
                    f"📍 {listing['district']}\n"
                    f"💰 {listing['price']} руб.\n"
                    f"👤 Клиент: {callback.from_user.full_name} (@{callback.from_user.username or 'нет имени пользователя'})\n"
                    f"🆔 ID: {callback.from_user.id}")
            await callback.message.bot.send_message(ADMIN_ID, text)
            response = await callback.message.answer(
                "Спасибо за интерес! Риэлтор свяжется с вами.",
                reply_markup=get_start_reply_keyboard()
            )
            data = await state.get_data()
            search_message_ids = data.get("search_message_ids", [])
            if callback.message.message_id not in search_message_ids:
                search_message_ids.append(callback.message.message_id)
                logging.debug(f"Добавлен message_id={callback.message.message_id} в process_interested (callback)")
            if response.message_id not in search_message_ids:
                search_message_ids.append(response.message_id)
                logging.debug(f"Добавлен message_id={response.message_id} в process_interested (ответ)")
            await state.update_data(search_message_ids=list(set(search_message_ids)))
            logging.info(f"Клиент {callback.from_user.id} заинтересован в объекте {listing_id}")
        else:
            response = await callback.message.answer(
                "Объект не найден. Попробуйте еще раз.",
                reply_markup=get_start_reply_keyboard()
            )
            data = await state.get_data()
            search_message_ids = data.get("search_message_ids", [])
            if response.message_id not in search_message_ids:
                search_message_ids.append(response.message_id)
                logging.debug(f"Добавлен message_id={response.message_id} в process_interested (объект не найден)")
            await state.update_data(search_message_ids=list(set(search_message_ids)))
            logging.warning(f"Объект {listing_id} не найден в таблице")
    except gspread.exceptions.GSpreadException as e:
        response = await callback.message.answer(
            f"Ошибка в структуре таблицы: {str(e)}. Обратитесь к администратору.",
            reply_markup=get_start_reply_keyboard()
        )
        data = await state.get_data()
        search_message_ids = data.get("search_message_ids", [])
        if response.message_id not in search_message_ids:
            search_message_ids.append(response.message_id)
            logging.debug(f"Добавлен message_id={response.message_id} в process_interested (ошибка GSpread)")
        await state.update_data(search_message_ids=list(set(search_message_ids)))
        logging.error(f"Ошибка в структуре таблицы: {e}")
    except Exception as e:
        response = await callback.message.answer(
            f"Произошла ошибка: {str(e)}",
            reply_markup=get_start_reply_keyboard()
        )
        data = await state.get_data()
        search_message_ids = data.get("search_message_ids", [])
        if response.message_id not in search_message_ids:
            search_message_ids.append(response.message_id)
            logging.debug(f"Добавлен message_id={response.message_id} в process_interested (общая ошибка)")
        await state.update_data(search_message_ids=list(set(search_message_ids)))
        logging.error(f"Ошибка при обработке интереса для записи {listing_id}: {e}")
    await callback.answer()

@router.callback_query(F.data == "return_to_main")
async def process_return_to_main(callback: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        search_message_ids = list(set(data.get("search_message_ids", [])))
        chat_id = callback.message.chat.id
        bot = callback.message.bot
        logging.debug(f"Попытка удалить сообщения: {search_message_ids} в чате {chat_id}")
        
        # Удаляем сохраненные сообщения
        for message_id in search_message_ids:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
                logging.debug(f"Удалено сообщение {message_id} в чате {chat_id}")
            except aiogram.exceptions.TelegramBadRequest as e:
                logging.debug(f"Не удалось удалить сообщение {message_id} в чате {chat_id}: {e}")

        # Дополнительная очистка только сообщений бота
        current_message_id = callback.message.message_id
        for i in range(max(1, current_message_id - 100), current_message_id + 1):
            try:
                await bot.delete_message(chat_id=chat_id, message_id=i)
                logging.debug(f"Удалено сообщение {i} в чате {chat_id} (дополнительная очистка)")
            except aiogram.exceptions.TelegramBadRequest as e:
                logging.debug(f"Не удалось удалить сообщение {i} в чате {chat_id}: {e}")
        
        # Отправляем главное меню
        response = await callback.message.answer(
            "Добро пожаловать в YouMaklerBot! Я помогу вам найти недвижимость или связаться с риэлтором.",
            reply_markup=get_start_reply_keyboard()
        )
        await state.clear()
        logging.info(f"Пользователь {callback.from_user.id} вернулся в главное меню, message_id={response.message_id}")
    except Exception as e:
        response = await callback.message.answer(f"Произошла ошибка при возврате в меню: {str(e)}")
        logging.error(f"Ошибка при возврате в меню: {e}")
    await callback.answer()