from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import ADMIN_ID
import logging
from datetime import datetime
import sqlite3

router = Router()

# Фильтр для админа
def is_admin(user_id):
    return user_id in ADMIN_ID

# Инициализация базы данных
def init_db():
    with sqlite3.connect('user_actions.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS actions
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         user_id INTEGER,
                         username TEXT,
                         action TEXT,
                         timestamp TEXT)''')
        conn.commit()

# Логирование действий пользователей
def log_user_action(user_id, username, action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    action_str = f"ID: {user_id} (@{username or 'no_username'}) - {action} - {timestamp}"
    with sqlite3.connect('user_actions.db') as conn:
        conn.execute("INSERT INTO actions (user_id, username, action, timestamp) VALUES (?, ?, ?, ?)",
                     (user_id, username or 'no_username', action, timestamp))
        conn.commit()
    logging.info(action_str)

# Получение последних действий
def get_user_actions(limit=10):
    with sqlite3.connect('user_actions.db') as conn:
        cursor = conn.execute("SELECT user_id, username, action, timestamp FROM actions ORDER BY id DESC LIMIT ?", (limit,))
        return [f"ID: {row[0]} (@{row[1]}) - {row[2]} - {row[3]}" for row in cursor.fetchall()]

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав доступа к этой команде.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Посмотреть действия пользователей", callback_data="view_actions")]
    ])
    await message.answer("Добро пожаловать в панель администратора!", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "view_actions")
async def view_user_actions(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.")
        return
    actions = get_user_actions()
    if not actions:
        await callback.message.edit_text("Нет записей о действиях пользователей.")
    else:
        actions_text = "\n".join(actions)
        await callback.message.edit_text(f"Последние действия пользователей:\n{actions_text}")
    await callback.answer()

# Интеграция с другими хэндлерами (пример)
@router.callback_query(F.data.startswith("interested_"))
async def log_interested(callback: CallbackQuery):
    if is_admin(callback.from_user.id):
        return
    listing_id = callback.data.replace("interested_", "")
    action = f"Показано интерес к объекту ID: {listing_id}"
    log_user_action(callback.from_user.id, callback.from_user.username, action)
    await callback.answer()