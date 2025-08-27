"""
Обработчик административных функций бота.
Предоставляет интерфейс для администраторов, включая просмотр действий пользователей,
статистики заявок и истории.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import ADMIN_ID
import logging
from datetime import datetime
import sqlite3
from services.sheets import GoogleSheetsService

from services.error_handler import error_handler  # Импортируем декоратор

router = Router()
logger = logging.getLogger(__name__)

# Фильтр для админа
def is_admin(user_id):
    return user_id in ADMIN_ID if isinstance(ADMIN_ID, (list, tuple)) else user_id == ADMIN_ID

# Инициализация базы данных
def init_db():
    """
    Инициализирует базу данных для логирования действий пользователей.
    Создаёт таблицу actions, если она ещё не существует.
    """
    try:
        with sqlite3.connect('user_actions.db') as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS actions
                           (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            username TEXT,
                            action TEXT,
                            timestamp TEXT)''')
            conn.commit()
        logger.info("База данных user_actions.db инициализирована")
    except sqlite3.Error as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise

# Логирование действий пользователей
def log_user_action(user_id, username, action):
    """
    Логирует действие пользователя в базу данных и в логгер.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    action_str = f"ID: {user_id} (@{username or 'no_username'}) - {action} - {timestamp}"
    try:
        with sqlite3.connect('user_actions.db') as conn:
            conn.execute("INSERT INTO actions (user_id, username, action, timestamp) VALUES (?, ?, ?, ?)",
                         (user_id, username or 'no_username', action, timestamp))
            conn.commit()
        logger.info(action_str)
    except sqlite3.Error as e:
        logger.error(f"Ошибка при логировании действия: {e}")
        raise

# Получение последних действий
def get_user_actions(limit=10):
    """
    Получает последние действия пользователей из базы данных.
    """
    try:
        with sqlite3.connect('user_actions.db') as conn:
            cursor = conn.execute("SELECT user_id, username, action, timestamp FROM actions ORDER BY id DESC LIMIT ?", (limit,))
            return [f"ID: {row[0]} (@{row[1]}) - {row[2]} - {row[3]}" for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении действий пользователей: {e}")
        raise

# Получение статистики заявок (примерная реализация)
async def get_request_stats():
    """
    Получает статистику заявок из Google Sheets.
    """
    sheets_service = GoogleSheetsService()
    requests = await sheets_service.get_all_requests()
    if not requests:
        return "Нет данных о заявках."
    total_requests = len(requests)
    unique_users = len(set(req.get("user_id") for req in requests))
    return f"Всего заявок: {total_requests}\nУникальных пользователей: {unique_users}"

# Получение истории заявок
async def get_request_history(limit=10):
    """
    Получает последние заявки из Google Sheets.
    """
    sheets_service = GoogleSheetsService()
    requests = await sheets_service.get_all_requests()
    if not requests:
        return "Нет истории заявок."
    sorted_requests = sorted(requests, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
    return "\n".join([f"ID: {req.get('user_id')} - {req.get('timestamp')} - {req.get('property_id')}" for req in sorted_requests])

# Очистка логов действий
def clear_user_actions():
    """
    Очищает таблицу действий пользователей.
    """
    try:
        with sqlite3.connect('user_actions.db') as conn:
            conn.execute("DELETE FROM actions")
            conn.commit()
        logger.info("Логи действий пользователей очищены")
        return "Логи действий успешно очищены."
    except sqlite3.Error as e:
        logger.error(f"Ошибка при очистке логов: {e}")
        raise

@router.message(Command("admin"))
@error_handler(operation_name="Открытие админ-панели (/admin)")
async def admin_panel(message: Message):
    """
    Обработчик команды /admin.
    Показывает админ-панель для авторизованных пользователей.
    """
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав доступа.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Действия пользователей", callback_data="view_actions"),
            InlineKeyboardButton(text="📊 Статистика заявок", callback_data="view_stats")
        ],
        [
            InlineKeyboardButton(text="📋 История заявок", callback_data="view_requests"),
            InlineKeyboardButton(text="🗑 Очистить логи", callback_data="clear_logs")
        ]
    ])
    await message.answer("Добро пожаловать в панель администратора!", reply_markup=keyboard)
    log_user_action(message.from_user.id, message.from_user.username, "Открыт админ-панель")

@router.callback_query(lambda c: c.data == "view_actions")
@error_handler(operation_name="Просмотр действий пользователей")
async def view_user_actions(callback: CallbackQuery):
    """
    Обработчик для просмотра последних действий пользователей.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return
    actions = get_user_actions()
    if not actions:
        await callback.message.edit_text("Нет записей о действиях пользователей.")
    else:
        actions_text = "\n".join(actions)
        await callback.message.edit_text(f"Последние действия пользователей:\n{actions_text}")
    await callback.answer()

@router.callback_query(lambda c: c.data == "view_stats")
@error_handler(operation_name="Просмотр статистики заявок")
async def view_request_stats(callback: CallbackQuery):
    """
    Обработчик для просмотра статистики заявок.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return
    stats = await get_request_stats()
    await callback.message.edit_text(f"Статистика заявок:\n{stats}")
    await callback.answer()

@router.callback_query(lambda c: c.data == "view_requests")
@error_handler(operation_name="Просмотр истории заявок")
async def view_request_history(callback: CallbackQuery):
    """
    Обработчик для просмотра истории заявок.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return
    history = await get_request_history()
    await callback.message.edit_text(f"История заявок:\n{history}")
    await callback.answer()

@router.callback_query(lambda c: c.data == "clear_logs")
@error_handler(operation_name="Очистка логов")
async def confirm_clear_logs(callback: CallbackQuery):
    """
    Обработчик для подтверждения очистки логов.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="confirm_clear"),
            InlineKeyboardButton(text="❌ Нет", callback_data="cancel_clear")
        ]
    ])
    await callback.message.edit_text("Вы уверены, что хотите очистить логи действий?", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(lambda c: c.data == "confirm_clear")
@error_handler(operation_name="Подтверждение очистки логов")
async def execute_clear_logs(callback: CallbackQuery):
    """
    Обработчик для выполнения очистки логов после подтверждения.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return
    result = clear_user_actions()
    await callback.message.edit_text(result)
    await callback.answer()

@router.callback_query(lambda c: c.data == "cancel_clear")
@error_handler(operation_name="Отмена очистки логов")
async def cancel_clear_logs(callback: CallbackQuery):
    """
    Обработчик для отмены очистки логов.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return
    await callback.message.edit_text("Очистка логов отменена.")
    await callback.answer()

@router.callback_query(F.data.startswith("interested_"))
@error_handler(operation_name="Логирование интереса к объекту")
async def log_interested(callback: CallbackQuery):
    """
    Обработчик для логирования интереса пользователя к объекту.
    """
    if is_admin(callback.from_user.id):
        await callback.answer("Администраторы не логируются для этого действия.", show_alert=True)
        return
    listing_id = callback.data.replace("interested_", "")
    action = f"Показано интерес к объекту ID: {listing_id}"
    log_user_action(callback.from_user.id, callback.from_user.username, action)
    await callback.answer("Ваш интерес к объекту зафиксирован!")