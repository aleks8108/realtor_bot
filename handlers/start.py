"""
Обработчик базовых команд бота.
Содержит обработчики для команд /start, /help и основного меню,
обеспечивая хорошую отправную точку для пользователей.
"""

import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery  # Добавлен импорт CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.keyboards import create_main_keyboard, get_property_type_keyboard, get_contact_keyboard
from services.error_handler import error_handler
from states.search import SearchStates
from states.request import RequestStates
from handlers.admin import log_user_action  # Для логирования

# Создаем роутер для базовых команд
router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart())
@error_handler(operation_name="Запуск бота (/start)")
async def cmd_start(message: Message, state: FSMContext):
    # Обработчик команды /start.
    # Приветствует пользователя и показывает основные возможности бота.
    await state.clear()
    
    user_name = message.from_user.first_name or "друг"
    
    welcome_message = (
        f"👋 Привет, {user_name}!\n\n"
        f"🏠 Добро пожаловать в риэлторский бот!\n\n"
        f"Я помогу вам:\n"
        f"• 🔍 Найти подходящие объекты недвижимости\n"
        f"• 📋 Подать заявку на просмотр\n"
        f"• 📞 Связаться с нашими специалистами\n\n"
        f"Выберите действие в меню ниже:"
    )
    
    await message.reply(
        welcome_message,
        reply_markup=create_main_keyboard(),
        parse_mode='HTML'
    )
    
    logger.info(f"Новый пользователь запустил бота: {message.from_user.id} (@{message.from_user.username})")

@router.message(Command("help"))
@error_handler(operation_name="Показ справки (/help)")
async def cmd_help(message: Message, state: FSMContext):
    """
    Обработчик команды /help.
    Предоставляет подробную информацию о возможностях бота.
    """
    help_message = (
        f"❓ <b>Справка по использованию бота</b>\n\n"
        f"<b>📋 Основные функции:</b>\n"
        f"• <i>Поиск объектов</i> - просмотр всех доступных объектов недвижимости\n"
        f"• <i>Подача заявки</i> - оформление заявки на просмотр объекта\n"
        f"• <i>Навигация</i> - удобное перемещение между объектами\n\n"
        f"<b>🎯 Как использовать:</b>\n"
        f"1️⃣ Нажмите '🔍 Поиск объектов' для просмотра доступных вариантов\n"
        f"2️⃣ Используйте кнопки ⬅️➡️ для навигации между объектами\n"
        f"3️⃣ Нажмите '📸 Фото' для просмотра изображений объекта\n"
        f"4️⃣ Нажмите '📋 Подать заявку' для оформления заявки на просмотр\n\n"
        f"<b>⚙️ Команды:</b>\n"
        f"/start - перезапустить бота\n"
        f"/help - показать эту справку\n"
        f"/cancel - отменить текущее действие\n\n"
        f"<b>📞 Нужна помощь?</b>\n"
        f"Если у вас возникли вопросы, наши менеджеры всегда готовы помочь!"
    )
    
    await message.reply(
        help_message,
        reply_markup=create_main_keyboard(),
        parse_mode='HTML'
    )

@router.message(F.text == "🏠 Главное меню")
@error_handler(operation_name="Возврат в главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    """
    Обработчик возврата в главное меню.
    Очищает состояние и показывает основные опции.
    """
    await state.clear()
    
    await message.reply(
        "🏠 Главное меню\n\n"
        "Выберите действие:",
        reply_markup=create_main_keyboard()
    )

@router.message(F.text == "📞 Контакты")
@error_handler(operation_name="Показ контактов")
async def show_contacts(message: Message):
    """
    Показывает контактную информацию компании.
    """
    contacts_message = (
        f"📞 <b>Контактная информация</b>\n\n"
        f"🏢 <b>Наша компания</b>\n"
        f"Агентство недвижимости 'ДомСервис'\n\n"
        f"📱 <b>Телефоны:</b>\n"
        f"• Отдел продаж: +7 (XXX) XXX-XX-XX\n"
        f"• Отдел аренды: +7 (XXX) XXX-XX-XX\n\n"
        f"🕐 <b>Режим работы:</b>\n"
        f"Пн-Пт: 9:00 - 19:00\n"
        f"Сб-Вс: 10:00 - 17:00\n\n"
        f"📍 <b>Адрес офиса:</b>\n"
        f"г. Москва, ул. Примерная, д. 123\n\n"
        f"💬 Или просто воспользуйтесь ботом для подачи заявки!"
    )
    
    await message.reply(
        contacts_message,
        reply_markup=create_main_keyboard(),
        parse_mode='HTML'
    )

@router.message(Command("search"))
@error_handler(operation_name="Запуск поиска (/search)")
async def cmd_search(message: Message, state: FSMContext):
    """
    Альтернативный способ запуска поиска через команду.
    Перенаправляет на процесс поиска с установкой начального состояния.
    """
    await state.set_state(SearchStates.awaiting_property_type)
    await message.answer(
        "Выберите тип недвижимости:",
        reply_markup=get_property_type_keyboard()  # Используем готовую клавиатуру для выбора типа
    )
    logger.info(f"Пользователь {message.from_user.id} запустил поиск через /search")

@router.message()
@error_handler(operation_name="Обработка неизвестной команды")
async def handle_unknown_message(message: Message):
    """
    Обработчик неизвестных сообщений.
    Помогает пользователям понять, как правильно использовать бота.
    """
    unknown_message = (
        f"🤔 Я не понимаю эту команду.\n\n"
        f"Воспользуйтесь кнопками меню или командами:\n"
        f"• /start - главное меню\n"
        f"• /help - справка\n"
        f"• /search - поиск объектов\n\n"
        f"Или просто нажмите нужную кнопку ниже:"
    )
    
    await message.reply(
        unknown_message,
        reply_markup=create_main_keyboard()
    )

# Добавляем обработчики для инлайн-кнопок

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
        reply_markup=get_property_type_keyboard()  # Используем клавиатуру для выбора типа
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
    await state.set_state(RequestStates.name)  # Используем 'name' вместо 'waiting_for_name'
    await callback.message.answer("Введите ваше имя:")
    await callback.answer("Начало подачи заявки...")
    logger.info(f"Пользователь {callback.from_user.id} начал подачу заявки")

@router.callback_query(F.data == "phone_info")
async def show_phone_info(callback: CallbackQuery):
    await callback.answer("Номер телефона: +7 905 476 44 48. Нажмите, чтобы позвонить.", show_alert=True)

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
        f"• Отдел аренды: +7 (XXX) XXX-XX-XX\n\n"
        f"🕐 <b>Режим работы:</b>\n"
        f"Пн-Пт: 9:00 - 19:00\n"
        f"Сб-Вс: 10:00 - 17:00\n\n"
        f"📍 <b>Адрес офиса:</b>\n"
        f"г. Москва, ул. Примерная, д. 123\n\n"
        f"💬 Или просто напишите в Telegram: @aleks8108"
    )
    await callback.message.answer(
        contacts_message,
        reply_markup=get_contact_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer("Контакты показаны")
    logger.info(f"Пользователь {callback.from_user.id} запросил контакты")