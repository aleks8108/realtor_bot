import logging
import traceback
from typing import Optional, Callable, Any, Union
from functools import wraps
import asyncio

from aiogram.types import Message, CallbackQuery, Update
from aiogram import Bot

# Импорт исключений
try:
    from exceptions.custom_exceptions import (
        BotException, GoogleSheetsError, ValidationError, 
        ListingNotFoundError, StateError, PhotoProcessingError
    )
except ImportError:
    class BotException(Exception):
        def __init__(self, message: str):
            self.message = message
            super().__init__(message)
    
    class GoogleSheetsError(BotException): pass
    class ValidationError(BotException): pass
    class ListingNotFoundError(BotException): pass
    class StateError(BotException): pass
    class PhotoProcessingError(BotException): pass

from utils.keyboards import get_main_menu

logger = logging.getLogger(__name__)

class ErrorHandler:
    @staticmethod
    async def handle_error(
        error: Exception, 
        message: Optional[Message] = None, 
        callback: Optional[CallbackQuery] = None,
        update: Optional[Update] = None,
        user_context: str = "Неизвестная операция"
    ) -> None:
        user_id = None
        bot = None
        chat_id = None
        
        if message:
            user_id = message.from_user.id if message.from_user else None
            bot = message.bot
            chat_id = message.chat.id
        elif callback:
            user_id = callback.from_user.id if callback.from_user else None
            bot = callback.bot if hasattr(callback, 'bot') else None
            chat_id = callback.message.chat.id if callback.message else None
        elif update:
            if update.message:
                user_id = update.message.from_user.id if update.message.from_user else None
                bot = update.message.bot if hasattr(update.message, 'bot') else None
                chat_id = update.message.chat.id
            elif update.callback_query:
                user_id = update.callback_query.from_user.id if update.callback_query.from_user else None
                bot = update.callback_query.bot if hasattr(update.callback_query, 'bot') else None
                chat_id = update.callback_query.message.chat.id if update.callback_query.message else None
        
        if not bot or not chat_id:
            logger.warning(f"Не удалось отправить сообщение об ошибке: bot={bot}, chat_id={chat_id}")
            return

        logger.error(
            f"Ошибка в операции '{user_context}' для пользователя {user_id}: "
            f"{type(error).__name__}: {str(error)}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        user_message = ErrorHandler._get_user_message(error)
        
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=user_message,
                reply_markup=get_main_menu()
            )
        except Exception as send_error:
            logger.error(f"Не удалось отправить сообщение об ошибке пользователю {user_id}: {send_error}")
        
        if callback:
            try:
                await callback.answer("Произошла ошибка. Попробуйте позже.")
            except Exception:
                pass
    
    @staticmethod
    def _get_user_message(error: Exception) -> str:
        if isinstance(error, ValidationError):
            return f"Ошибка в данных: {error.message}\nПожалуйста, проверьте введенную информацию."
        elif isinstance(error, GoogleSheetsError):
            return ("Временные проблемы с сервисом. Мы уже работаем над решением.\n"
                   "Попробуйте повторить операцию через несколько минут.")
        elif isinstance(error, ListingNotFoundError):
            return "Объект недвижимости не найден или больше не доступен."
        elif isinstance(error, StateError):
            return ("Произошел сбой в обработке вашего запроса.\n"
                   "Пожалуйста, начните операцию заново.")
        elif isinstance(error, PhotoProcessingError):
            return "Проблема с загрузкой фотографий объекта. Попробуйте позже."
        elif isinstance(error, BotException):
            return error.message
        else:
            return ("Произошла непредвиденная ошибка. Мы уже уведомлены о проблеме.\n"
                   "Пожалуйста, попробуйте позже или свяжитесь с поддержкой.")

def error_handler(operation_name: str = "Неизвестная операция"):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                message = None
                callback = None
                update = None
                
                for arg in args:
                    if isinstance(arg, Message):
                        message = arg
                        break
                    elif isinstance(arg, CallbackQuery):
                        callback = arg
                        break
                    elif isinstance(arg, Update):
                        update = arg
                        break
                
                await ErrorHandler.handle_error(
                    error=e, 
                    message=message, 
                    callback=callback,
                    update=update,
                    user_context=operation_name
                )
                return None
        return wrapper
    return decorator

async def retry_operation(
    operation: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    operation_name: str = "Неизвестная операция"
) -> Any:
    if not asyncio.iscoroutinefunction(operation):
        raise ValueError("Операция должна быть корутиной")
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = delay * (backoff_factor ** attempt)
                logger.warning(
                    f"Операция '{operation_name}' - попытка {attempt + 1}/{max_retries + 1} неудачна: {e}. "
                    f"Повтор через {wait_time:.2f} сек."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Операция '{operation_name}' - все {max_retries + 1} попыток исчерпаны")
    
    raise last_exception

def setup_global_error_handler(bot: Bot):
    async def global_error_handler(update: Update, exception: Exception):
        await ErrorHandler.handle_error(
            error=exception,
            update=update,
            user_context="Глобальная обработка"
        )
    
    bot.register_error_handler(global_error_handler)
    return global_error_handler

# Удаляем дублирующие функции, используя handle_error напрямую
# async def handle_message_error(error: Exception, message: Message, context: str = "Обработка сообщения"):
#     await ErrorHandler.handle_error(error, message=message, user_context=context)
#
# async def handle_callback_error(error: Exception, callback: CallbackQuery, context: str = "Обработка callback"):
#     await ErrorHandler.handle_error(error, callback=callback, user_context=context)