"""
Сервис для централизованной обработки ошибок в боте.
Этот модуль обеспечивает единообразную обработку исключений и логирование ошибок.
"""

import logging
import traceback
from typing import Optional, Callable, Any
from functools import wraps
import asyncio

from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from exceptions.custom_exceptions import (
    BotException, GoogleSheetsError, ValidationError, 
    ListingNotFoundError, StateError, PhotoProcessingError
)
from utils.keyboards import get_main_menu


# Настройка логгера для обработки ошибок
logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Класс для централизованной обработки ошибок бота.
    Обеспечивает логирование ошибок и отправку понятных сообщений пользователям.
    """
    
    @staticmethod
    async def handle_errors(
        error: Exception, 
        message: Optional[Message] = None, 
        callback: Optional[CallbackQuery] = None,
        user_context: str = "Неизвестная операция"
    ) -> None:
        """
        Основной метод обработки ошибок.
        
        Args:
            error: Исключение для обработки
            message: Объект сообщения (для text handler'ов)
            callback: Объект callback'а (для callback handler'ов) 
            user_context: Описание операции для логирования
        """
        user_id = None
        bot = None
        chat_id = None
        
        # Определяем источник ошибки и извлекаем необходимые объекты
        if message:
            user_id = message.from_user.id if message.from_user else None
            bot = message.bot
            chat_id = message.chat.id
        elif callback:
            user_id = callback.from_user.id if callback.from_user else None
            bot = callback.bot if callback.message else None
            chat_id = callback.message.chat.id if callback.message else None
        
        # Логируем ошибку с контекстом
        logger.error(
            f"Ошибка в операции '{user_context}' для пользователя {user_id}: "
            f"{type(error).__name__}: {str(error)}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        # Определяем пользовательское сообщение на основе типа ошибки
        user_message = ErrorHandler._get_user_message(error)
        
        # Отправляем сообщение пользователю, если возможно
        if bot and chat_id:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=user_message,
                    reply_markup=get_main_menu()
                )
            except Exception as send_error:
                logger.error(f"Не удалось отправить сообщение об ошибке пользователю {user_id}: {send_error}")
        
        # Для callback'ов отвечаем на запрос
        if callback:
            try:
                await callback.answer("Произошла ошибка. Попробуйте позже.")
            except Exception:
                pass  # Игнорируем ошибки при ответе на callback
    
    @staticmethod
    def _get_user_message(error: Exception) -> str:
        """
        Возвращает понятное пользователю сообщение на основе типа ошибки.
        Это помогает скрыть технические детали и дать пользователю четкие инструкции.
        """
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
    """
    Декоратор для автоматической обработки ошибок в handler'ах.
    Использование: @error_handler("Подача заявки")
    
    Args:
        operation_name: Название операции для логирования
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Пытаемся найти Message или CallbackQuery в аргументах
                message = None
                callback = None
                
                for arg in args:
                    if isinstance(arg, Message):
                        message = arg
                        break
                    elif isinstance(arg, CallbackQuery):
                        callback = arg
                        break
                
                await ErrorHandler.handle_error(
                    error=e, 
                    message=message, 
                    callback=callback, 
                    user_context=operation_name
                )
                return None  # Возвращаем None вместо propagation ошибки
        return wrapper
    return decorator


async def retry_operation(
    operation: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Any:
    """
    Выполняет операцию с повторными попытками при ошибках.
    Полезно для работы с внешними API, которые могут временно не отвечать.
    
    Args:
        operation: Async функция для выполнения
        max_retries: Максимальное количество повторов
        delay: Базовая задержка между попытками
        backoff_factor: Множитель увеличения задержки
    
    Returns:
        Результат выполнения операции
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries:
                wait_time = delay * (backoff_factor ** attempt)
                logger.warning(
                    f"Попытка {attempt + 1}/{max_retries + 1} неудачна: {e}. "
                    f"Повтор через {wait_time:.2f} сек."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Все {max_retries + 1} попыток исчерпаны для операции")
    
    # Если все попытки исчерпаны, поднимаем последнее исключение
    raise last_exception