from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.sheets import init_sheets
from config import ADMIN_ID
from keyboards.search_filters import get_property_type_keyboard, get_deal_type_keyboard, get_district_keyboard
import logging
import gspread  # Added to resolve Pylance errors

router = Router()

class SearchStates(StatesGroup):
    property_type = State()
    deal_type = State()
    district = State()
    budget = State()
    rooms = State()

@router.message(F.text == "🏠 Найти недвижимость")
async def start_search(message: types.Message, state: FSMContext):
    logging.info(f"Кнопка 'Найти недвижимость' нажата пользователем {message.from_user.id}")
    await message.answer("Выберите тип недвижимости:", reply_markup=get_property_type_keyboard())
    await state.set_state(SearchStates.property_type)

@router.callback_query(SearchStates.property_type)
async def process_property_type(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(property_type=callback.data)
    await callback.message.edit_text("Выберите тип сделки:", reply_markup=get_deal_type_keyboard())
    await state.set_state(SearchStates.deal_type)
    await callback.answer()

@router.callback_query(SearchStates.deal_type)
async def process_deal_type(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(deal_type=callback.data)
    await callback.message.edit_text("Выберите район:", reply_markup=get_district_keyboard())
    await state.set_state(SearchStates.district)
    await callback.answer()

@router.callback_query(SearchStates.district)
async def process_district(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(district=callback.data)
    await callback.message.edit_text("Введите бюджет (например, 1000000-5000000):")
    await state.set_state(SearchStates.budget)
    await callback.answer()

@router.message(SearchStates.budget)
async def process_budget(message: types.Message, state: FSMContext):
    budget = message.text.strip()
    if not validate_budget(budget):
        await message.answer("Пожалуйста, введите бюджет в формате 'от-до' (например, 1000000-5000000).")
        return
    await state.update_data(budget=budget)
    data = await state.get_data()
    if data["property_type"] in ["Квартира", "Коммерческая"]:
        await message.answer("Введите количество комнат (например, 2) или пропустите, нажав Enter для 'Любое':")
        await state.set_state(SearchStates.rooms)
    else:
        await perform_search(message, state)

@router.message(SearchStates.rooms)
async def process_rooms(message: types.Message, state: FSMContext):
    rooms = message.text.strip() or "Любое"
    if rooms != "Любое" and not rooms.isdigit():
        await message.answer("Пожалуйста, введите число комнат (например, 2) или пропустите (Enter).")
        return
    await state.update_data(rooms=rooms)
    await perform_search(message, state)

def validate_budget(budget: str) -> bool:
    try:
        min_budget, max_budget = map(int, budget.split("-"))
        if min_budget <= 0 or max_budget < min_budget:
            return False
        return True
    except ValueError:
        return False

async def perform_search(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        logging.info(f"Поиск с фильтрами: {data}")
        sheet = init_sheets()
        listings = sheet.get_all_records()
        logging.info(f"Получено записей из таблицы: {len(listings)}")

        filtered_listings = []
        for listing in listings:
            if not is_valid_listing(listing, data):
                continue
            filtered_listings.append(listing)
        filtered_listings = filtered_listings[:5]

        if not filtered_listings:
            await message.answer("К сожалению, ничего не найдено. Попробуйте изменить фильтры.")
            logging.info("Результаты поиска: ничего не найдено")
            await state.clear()
            return

        for listing in filtered_listings:
            text = (f"🏠 {listing['property_type']} ({listing['deal_type']})\n"
                    f"📍 {listing['district']}\n"
                    f"💰 {listing['price']} руб.\n"
                    f"🛋 Комнат: {listing.get('rooms', 'Не указано')}\n"
                    f"📝 {listing.get('description', 'Нет описания')}")
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Интересует", callback_data=f"interested_{listing['id']}")]
            ])
            if listing.get("photo_url"):
                try:
                    await message.answer_photo(
                        photo=listing["photo_url"],
                        caption=text,
                        reply_markup=markup
                    )
                except Exception as e:
                    logging.warning(f"Ошибка отправки фото {listing['photo_url']}: {e}")
                    await message.answer(text, reply_markup=markup)
            else:
                await message.answer(text, reply_markup=markup)

        logging.info(f"Отправлено {len(filtered_listings)} результатов поиска")
        await state.clear()
    except gspread.exceptions.GSpreadException as e:
        await message.answer(f"Ошибка в структуре таблицы: {str(e)}. Обратитесь к администратору.")
        logging.error(f"Ошибка в структуре таблицы: {e}")
        await state.clear()
    except Exception as e:
        await message.answer(f"Произошла ошибка при поиске: {str(e)}")
        logging.error(f"Ошибка при поиске: {e}")
        await state.clear()

def is_valid_listing(listing: dict, data: dict) -> bool:
    try:
        # Проверка property_type
        listing_property_type = str(listing.get("property_type", "")).strip()
        if listing_property_type != data["property_type"]:
            logging.debug(f"Запись {listing.get('id')} отклонена: property_type={listing_property_type} != {data['property_type']}")
            return False

        # Проверка deal_type
        listing_deal_type = str(listing.get("deal_type", "")).strip()
        if listing_deal_type != data["deal_type"]:
            logging.debug(f"Запись {listing.get('id')} отклонена: deal_type={listing_deal_type} != {data['deal_type']}")
            return False

        # Проверка district
        listing_district = str(listing.get("district", "")).strip()
        if listing_district != data["district"]:
            logging.debug(f"Запись {listing.get('id')} отклонена: district={listing_district} != {data['district']}")
            return False

        # Проверка бюджета
        price = listing.get("price", 0)
        if isinstance(price, str):
            if not price.strip().isdigit():
                logging.warning(f"Некорректная цена в записи {listing.get('id')}: {price}")
                return False
            price = int(price)
        elif not isinstance(price, int):
            logging.warning(f"Некорректный тип цены в записи {listing.get('id')}: {type(price)}")
            return False
        if not is_in_budget(price, data["budget"]):
            logging.debug(f"Запись {listing.get('id')} отклонена: price={price} не в бюджете {data['budget']}")
            return False

        # Проверка количества комнат
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
        min_budget, max_budget = map(int, budget.split("-"))
        result = min_budget <= price <= max_budget
        logging.debug(f"Проверка бюджета: price={price}, budget={min_budget}-{max_budget}, результат={result}")
        return result
    except ValueError as e:
        logging.warning(f"Ошибка при проверке бюджета: price={price}, budget={budget}, ошибка={e}")
        return False

@router.callback_query(F.data.startswith("interested_"))
async def process_interested(callback: types.CallbackQuery):
    try:
        listing_id = callback.data.split("_")[1]
        sheet = init_sheets()
        listings = sheet.get_all_records()
        listing = next((l for l in listings if str(l["id"]) == listing_id), None)
        
        if listing:
            text = (f"Клиент заинтересован в объекте:\n"
                    f"🏠 {listing['property_type']} ({listing['deal_type']})\n"
                    f"📍 {listing['district']}\n"
                    f"💰 {listing['price']} руб.\n"
                    f"👤 Клиент: {callback.from_user.full_name} (@{callback.from_user.username or 'нет имени пользователя'})\n"
                    f"🆔 ID: {callback.from_user.id}")
            await callback.message.bot.send_message(ADMIN_ID, text)
            await callback.message.answer("Спасибо за интерес! Риэлтор свяжется с вами.")
            logging.info(f"Клиент {callback.from_user.id} заинтересован в объекте {listing_id}")
        else:
            await callback.message.answer("Объект не найден. Попробуйте еще раз.")
            logging.warning(f"Объект {listing_id} не найден")
    except gspread.exceptions.GSpreadException as e:
        await callback.message.answer(f"Ошибка в структуре таблицы: {str(e)}. Обратитесь к администратору.")
        logging.error(f"Ошибка в структуре таблицы: {e}")
    except Exception as e:
        await callback.message.answer(f"Произошла ошибка: {str(e)}")
        logging.error(f"Ошибка при обработке интереса: {e}")
    await callback.answer()