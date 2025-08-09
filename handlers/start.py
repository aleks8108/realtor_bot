"""
Обработчик базовых команд бота.
Содержит обработчики для команд /start, /help и основного меню,
обеспечивая хорошую отправную точку для пользователей.
"""

import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils.keyboards import create_main_keyboard
from services.error_handler import handle_errors, ErrorHandler

# Создаем роутер для базовых команд
router = Router()
error_handler = ErrorHandler()

logger = logging.getLogger(__name__)


@router.message(CommandStart())
@handle_errors(error_handler)
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    Приветствует пользователя и показывает основные возможности бота.
    """
    # Очищаем любые активные состояния
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
@handle_errors(error_handler)
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
@handle_errors(error_handler)
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
@handle_errors(error_handler)
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
@handle_errors(error_handler)
async def cmd_search(message: Message, state: FSMContext):
    """
    Альтернативный способ запуска поиска через команду.
    Перенаправляет на обработчик поиска из search модуля.
    """
    # Имитируем нажатие кнопки "Поиск объектов"
    from handlers.search import start_search
    
    # Изменяем текст сообщения для совместимости с обработчиком
    message.text = "🔍 Поиск объектов"
    await start_search(message, state)


@router.message()
@handle_errors(error_handler)
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