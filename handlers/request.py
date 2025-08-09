
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from states.request import RequestStates
from services.sheets import save_request, get_listings
from config import ADMIN_ID
from utils.keyboards import get_property_type_keyboard, get_deal_type_keyboard, get_district_keyboard, get_budget_keyboard, get_start_reply_keyboard, get_rooms_keyboard, get_listing_menu, get_menu_and_clear_buttons, get_main_menu
import logging
import asyncio

logging.basicConfig(filename='bot.log', level=logging.INFO, encoding='utf-8')
router = Router()

@router.message(F.text == "📝 Оставить заявку")
async def start_request(message: types.Message, state: FSMContext):
    logging.info(f"Запуск процесса заявки для пользователя {message.from_user.id}")
    await message.answer("Введите ваше имя:", reply_markup=get_menu_and_clear_buttons())
    await state.set_state(RequestStates.name)

@router.message(RequestStates.name)
async def process_name(message: types.Message, state: FSMContext):
    logging.info(f"Получено имя от пользователя {message.from_user.id}: {message.text}")
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
    logging.info(f"Получен телефон от пользователя {message.from_user.id}")
    phone = message.contact.phone_number if message.contact else message.text.strip()
    if not phone or not any(c.isdigit() for c in phone):
        await message.answer("Пожалуйста, введите корректный номер телефона.", reply_markup=get_menu_and_clear_buttons())
        return
    await state.update_data(phone=phone)
    await message.answer("Выберите тип недвижимости:", reply_markup=get_property_type_keyboard())
    await state.set_state(RequestStates.property_type)

@router.callback_query(RequestStates.property_type)
async def process_property_type(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Выбран тип недвижимости от пользователя {callback.from_user.id}: {callback.data}")
    await state.update_data(property_type=callback.data)
    try:
        await callback.message.edit_text("Выберите тип сделки:", reply_markup=get_deal_type_keyboard())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        elif "there is no text in the message to edit" in str(e):
            await callback.message.answer("Выберите тип сделки:", reply_markup=get_deal_type_keyboard())
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            await callback.message.answer("Выберите тип сделки:", reply_markup=get_deal_type_keyboard())
    await state.set_state(RequestStates.deal_type)
    await callback.answer()

@router.callback_query(RequestStates.deal_type)
async def process_deal_type(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Выбран тип сделки от пользователя {callback.from_user.id}: {callback.data}")
    await state.update_data(deal_type=callback.data)
    try:
        await callback.message.edit_text("Выберите район:", reply_markup=get_district_keyboard())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            await callback.message.edit_text("Выберите район:", reply_markup=get_district_keyboard())
    await state.set_state(RequestStates.district)
    await callback.answer()

@router.callback_query(RequestStates.district)
async def process_district(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Выбран район от пользователя {callback.from_user.id}: {callback.data}")
    await state.update_data(district=callback.data)
    try:
        await callback.message.edit_text("Выберите бюджет:", reply_markup=get_budget_keyboard())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            await callback.message.edit_text("Выберите бюджет:", reply_markup=get_budget_keyboard())
    await state.set_state(RequestStates.budget)
    await callback.answer()

@router.callback_query(RequestStates.budget)
async def process_budget(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Выбран бюджет от пользователя {callback.from_user.id}: {callback.data}")
    await state.update_data(budget=callback.data)
    try:
        await callback.message.edit_text("Выберите количество комнат:", reply_markup=get_rooms_keyboard())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            await callback.message.edit_text("Выберите количество комнат:", reply_markup=get_rooms_keyboard())
    await state.set_state(RequestStates.rooms)
    await callback.answer()

@router.callback_query(RequestStates.rooms)
async def process_rooms(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Выбрано количество комнат от пользователя {callback.from_user.id}: {callback.data}")
    rooms = callback.data.split('_')[1] if callback.data.startswith('rooms_') else None
    await state.update_data(rooms=rooms)
    data = await state.get_data()
    required_fields = ['name', 'phone', 'property_type', 'deal_type', 'district', 'budget']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logging.error(f"Отсутствуют обязательные поля: {missing_fields}")
        await callback.message.answer("Произошла ошибка. Пожалуйста, начните заново.", reply_markup=get_main_menu())
        await state.clear()
        await callback.answer()
        return

    try:
        listings = get_listings()
    except Exception as e:
        logging.error(f"Ошибка при получении данных из Google Sheets: {e}")
        listings = []

    filtered_listings = [
        l for l in listings
        if l.get('property_type') == data['property_type'].replace("property_type_", "") and
           l.get('deal_type') == data['deal_type'].replace("deal_type_", "") and
           l.get('district') == data['district'].replace("district_", "") and
           float(l.get('price', 0)) <= float(data['budget'].replace("budget_", "").split('-')[-1]) and
           (data['rooms'] is None or str(l.get('rooms', '')) == str(data['rooms']))
    ]

    await state.update_data(filtered_listings=filtered_listings, current_listing_index=0, current_photo_index=0)

    if filtered_listings:
        listing = filtered_listings[0]
        photo_urls = (
            [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
            if isinstance(listing.get('photo_url'), str) else
            [url.strip() for url in listing.get('photo_url', []) if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
        )
        message_text = f"Объект 1/{len(filtered_listings)}\nID: {listing['id']}\n{listing.get('description', 'Нет описания')}\nЦена: {listing['price']} ₽\n\nПожалуйста, введите комментарий к заявке (или напишите 'Без комментариев'):"
        keyboard = get_listing_menu(
            listing_exists=True,
            comments_provided=False,
            has_next_listing=len(filtered_listings) > 1,
            listing_index=0,
            photo_index=0,
            total_photos=len(photo_urls),
            total_listings=len(filtered_listings),
            listing_id=listing['id']
        )
        sent_message = await callback.message.answer(message_text, reply_markup=keyboard)
        if photo_urls:
            await callback.message.answer_photo(photo=photo_urls[0])
    else:
        message_text = "Объект с указанными параметрами не найден. Рекомендуем завершить заявку — риэлтор свяжется с вами.\n\nПожалуйста, введите комментарий к заявке (или напишите 'Без комментариев'):"
        keyboard = get_listing_menu(listing_exists=False, comments_provided=False)
        sent_message = await callback.message.answer(message_text, reply_markup=keyboard)

    await state.set_state(RequestStates.listing)
    logging.debug(f"Состояние установлено: {await state.get_state()}")
    await callback.answer()

@router.message(RequestStates.listing)
async def process_listing_comments(message: Message, state: FSMContext):
    logging.info(f"Получены комментарии от пользователя {message.from_user.id}: {message.text}")
    current_state = await state.get_state()
    logging.debug(f"Текущее состояние: {current_state}")
    comments = message.text.strip() if message.text and message.text.strip() else "Без комментариев"
    await state.update_data(comments=comments)
    data = await state.get_data()
    filtered_listings = data.get('filtered_listings', [])
    listing_exists = bool(filtered_listings)

    logging.debug(f"Обработка комментария: listing_exists={listing_exists}, comments={comments}, state={current_state}")

    # Автоматическое завершение заявки
    request_data = {
        "name": data.get("name", ""),
        "phone": data.get("phone", ""),
        "property_type": data.get("property_type", "").replace("property_type_", ""),
        "deal_type": data.get("deal_type", "").replace("deal_type_", ""),
        "district": data.get("district", "").replace("district_", ""),
        "budget": data.get("budget", "").replace("budget_", ""),
        "rooms": data.get("rooms", ""),
        "comments": comments,
        "user_id": message.from_user.id,
        "username": message.from_user.username or "no_username"
    }
    logging.info(f"Попытка сохранить заявку: {request_data}")

    # Сохранение в Google Sheets
    try:
        save_request(request_data)
        logging.info("Заявка успешно сохранена в Google Sheets")
    except Exception as e:
        logging.error(f"Ошибка при сохранении заявки в Google Sheets: {e}")
        await message.answer("Ошибка при сохранении заявки. Попробуйте позже.", reply_markup=get_main_menu())
        await state.clear()
        return

    # Уведомление админу
    if ADMIN_ID and isinstance(ADMIN_ID, (list, tuple)) and ADMIN_ID:
        admin_message = (
            f"Новая заявка от пользователя {message.from_user.id} (@{message.from_user.username or 'no_username'}):\n"
            f"Имя: {request_data['name']}\nТелефон: {request_data['phone']}\nТип: {request_data['property_type']}\n"
            f"Сделка: {request_data['deal_type']}\nРайон: {request_data['district']}\nБюджет: {request_data['budget']}\n"
            f"Комнаты: {request_data['rooms']}\nКомментарий: {request_data['comments']}"
        )
        try:
            await message.bot.send_message(ADMIN_ID[0], admin_message)
            logging.info(f"Уведомление админу отправлено для пользователя {message.from_user.id}")
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления админу: {e}")

    if listing_exists:
        current_listing_index = data.get('current_listing_index', 0)
        listing = filtered_listings[current_listing_index]
        photo_urls = (
            [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
            if isinstance(listing.get('photo_url'), str) else
            [url.strip() for url in listing.get('photo_url', []) if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
        )
        message_text = f"Ваш комментарий сохранён. Заявка успешно отправлена!\n\nОбъект {current_listing_index + 1}/{len(filtered_listings)}\nID: {listing['id']}\n{listing.get('description', 'Нет описания')}\nЦена: {listing['price']} ₽"
        keyboard = get_listing_menu(
            listing_exists=True,
            comments_provided=True,
            has_next_listing=current_listing_index < len(filtered_listings) - 1,
            listing_index=current_listing_index,
            photo_index=data.get('current_photo_index', 0),
            total_photos=len(photo_urls),
            total_listings=len(filtered_listings),
            listing_id=listing['id']
        )
        if photo_urls:
            await message.answer_photo(photo=photo_urls[data.get('current_photo_index', 0)], caption=message_text, reply_markup=keyboard)
        else:
            await message.answer(message_text, reply_markup=keyboard)
    else:
        message_text = "Ваш комментарий сохранён. Заявка успешно отправлена! Объект с указанными параметрами не найден. Риэлтор свяжется с вами."
        await message.answer(message_text, reply_markup=get_main_menu())

    await state.clear()
    await asyncio.sleep(0.5)
    await message.delete()

@router.callback_query(F.data.startswith("next_photo_"))
async def next_photo(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    filtered_listings = data.get('filtered_listings', [])
    if not filtered_listings:
        await callback.answer("Нет доступных объектов.")
        return
    
    current_index = data.get('current_listing_index', 0)
    listing = filtered_listings[current_index]
    photo_urls = (
        [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
        if isinstance(listing.get('photo_url'), str) else
        [url.strip() for url in listing.get('photo_url', []) if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
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
            comments_provided=bool(data.get('comments')),
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
async def prev_photo(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    filtered_listings = data.get('filtered_listings', [])
    if not filtered_listings:
        await callback.answer("Нет доступных объектов.")
        return
    
    current_index = data.get('current_listing_index', 0)
    listing = filtered_listings[current_index]
    photo_urls = (
        [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
        if isinstance(listing.get('photo_url'), str) else
        [url.strip() for url in listing.get('photo_url', []) if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
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
            comments_provided=bool(data.get('comments')),
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
async def next_listing(callback: CallbackQuery, state: FSMContext):
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
    photo_urls = (
        [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
        if isinstance(listing.get('photo_url'), str) else
        [url.strip() for url in listing.get('photo_url', []) if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
    )
    await state.update_data(current_listing_index=new_listing_index, current_photo_index=0)
    
    await callback.message.delete()
    message_text = f"Объект {new_listing_index + 1}/{len(filtered_listings)}\nID: {listing['id']}\n{listing['description']}\nЦена: {listing['price']} ₽"
    keyboard = get_listing_menu(
        listing_exists=True,
        comments_provided=bool(data.get('comments')),
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
async def prev_listing(callback: CallbackQuery, state: FSMContext):
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
    photo_urls = (
        [url.strip() for url in listing.get('photo_url', '').split(',') if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
        if isinstance(listing.get('photo_url'), str) else
        [url.strip() for url in listing.get('photo_url', []) if url.strip().startswith('http') and url.strip().endswith(('.jpg', '.jpeg', '.png'))]
    )
    await state.update_data(current_listing_index=new_listing_index, current_photo_index=0)
    
    await callback.message.delete()
    message_text = f"Объект {new_listing_index + 1}/{len(filtered_listings)}\nID: {listing['id']}\n{listing['description']}\nЦена: {listing['price']} ₽"
    keyboard = get_listing_menu(
        listing_exists=True,
        comments_provided=bool(data.get('comments')),
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
    listing_id = callback.data.replace("interested_", "")
    data = await state.get_data()
    filtered_listings = data.get('filtered_listings', [])
    listing = next((l for l in filtered_listings if str(l['id']) == listing_id), None)
    if not listing:
        await callback.answer("Объект не найден.")
        return
    
    await callback.bot.send_message(
        ADMIN_ID[0],
        f"Пользователь {callback.from_user.id} (@{callback.from_user.username or 'no_username'}) заинтересован в объекте ID: {listing_id}\n{listing['description']}\nЦена: {listing['price']} ₽"
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
        has_next_listing=len(filtered_listings) > 1,
        listing_index=current_listing_index,
        photo_index=data.get('current_photo_index', 0),
        total_photos=len(photo_urls),
        total_listings=len(filtered_listings),
        listing_id=listing['id']
    )
    await callback.message.answer(message_text, reply_markup=keyboard)
    if photo_urls:
        await callback.message.answer_photo(photo=photo_urls[data.get('current_photo_index', 0)])
    await callback.answer("Ваш интерес зафиксирован. Пожалуйста, введите комментарий.")
    logging.info(f"Пользователь {callback.from_user.id} заинтересован в объекте ID: {listing_id}")

@router.callback_query(lambda c: c.data == "clear_chat")
async def clear_chat(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Очистка чата от пользователя {callback.from_user.id}")
    try:
        await callback.message.delete()
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения: {e}")
    await state.clear()
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("return_to_menu"))
async def return_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Вы вернулись в главное меню.", reply_markup=get_main_menu())
    await callback.answer()