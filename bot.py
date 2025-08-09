"""
Главный файл риэлторского бота.
Этот модуль инициализирует бота, регистрирует все обработчики
и запускает основной цикл обработки сообщений.

Архитектура построена на принципах:
- Разделения ответственности (каждый модуль отвечает за свою область)
- Единой точки истины для конфигурации
- Централизованной обработки ошибок
- Слабой связанности компонентов
"""

import asyncio
import logging
import sys
from typing import Any, Awaitable, Callable, Dict

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем конфигурацию и обработчики
from config import BOT_TOKEN, LOG_LEVEL
from handlers import admin, request, search, start
from services.error_handler import ErrorHandler

# Настройка логирования для всего приложения
def setup_logging():
    """
    Настраивает систему логирования для всего приложения.
    Использует единый формат и уровень логирования для консистентности.
    """
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    # Снижаем уровень логирования для библиотек aiogram, чтобы уменьшить шум
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)


async def setup_bot_commands(bot: Bot):
    """
    Настраивает команды бота, которые будут отображаться в меню Telegram.
    Эта функция помогает пользователям понять доступные команды.
    """
    from aiogram.types import BotCommand
    
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="❓ Помощь"),
        BotCommand(command="search", description="🔍 Поиск объектов"),
        BotCommand(command="cancel", description="❌ Отменить текущее действие"),
    ]
    
    await bot.set_my_commands(commands)


def register_handlers(dp: Dispatcher):
    """
    Регистрирует все обработчики сообщений в диспетчере.
    Порядок регистрации важен - более специфичные обработчики должны быть первыми.
    """
    # Регистрируем роутеры в правильном порядке приоритета
    dp.include_router(admin.router)     # Административные команды (высокий приоритет)
    dp.include_router(request.router)   # Обработка заявок
    dp.include_router(search.router)    # Поиск и просмотр объектов
    dp.include_router(start.router)     # Базовые команды (низкий приоритет)


async def setup_error_handling(dp: Dispatcher):
    """
    Настраивает глобальную обработку ошибок для диспетчера.
    Это последний рубеж защиты от необработанных исключений.
    """
    error_handler = ErrorHandler()
    
    @dp.error()
    async def global_error_handler(event, data: Dict[str, Any]):
        """
        Глобальный обработчик ошибок для всего бота.
        Логирует ошибки и отправляет пользователю понятное сообщение.
        """
        try:
            if event.update.message:
                user_id = event.update.message.from_user.id
                await error_handler.handle_error(
                    event.exception,
                    event.update.message,
                    f"Глобальная ошибка для пользователя {user_id}"
                )
            elif event.update.callback_query:
                user_id = event.update.callback_query.from_user.id
                await error_handler.handle_callback_error(
                    event.exception,
                    event.update.callback_query,
                    f"Глобальная ошибка callback для пользователя {user_id}"
                )
            else:
                logging.error(f"Необработанная глобальная ошибка: {event.exception}")
                
        except Exception as e:
            logging.critical(f"Критическая ошибка в глобальном обработчике: {e}")


async def on_startup(bot: Bot):
    """
    Выполняется при запуске бота.
    Инициализирует необходимые ресурсы и настройки.
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Получаем информацию о боте для проверки токена
        bot_info = await bot.get_me()
        logger.info(f"Бот запущен: @{bot_info.username} ({bot_info.full_name})")
        
        # Настраиваем команды бота
        await setup_bot_commands(bot)
        logger.info("Команды бота настроены")
        
        # Проверяем доступность Google Sheets
        from services.sheets import GoogleSheetsService
        sheets_service = GoogleSheetsService()
        
        # Проверяем подключение (пытаемся получить первый объект)
        test_properties = await sheets_service.get_all_properties()
        logger.info(f"Google Sheets подключен. Найдено {len(test_properties) if test_properties else 0} объектов")
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise


async def on_shutdown(bot: Bot):
    """
    Выполняется при остановке бота.
    Освобождает ресурсы и выполняет финальную очистку.
    """
    logger = logging.getLogger(__name__)
    logger.info("Бот остановлен")


def create_bot() -> Bot:
    """
    Создает и настраивает экземпляр бота с необходимыми параметрами.
    Централизует настройку бота для консистентности.
    """
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")
    
    return Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,  # HTML по умолчанию для форматирования
            protect_content=False,      # Разрешаем пересылку сообщений
        )
    )


def create_dispatcher() -> Dispatcher:
    """
    Создает и настраивает диспетчер с хранилищем состояний.
    Использует MemoryStorage для простоты, но может быть легко заменено на Redis.
    """
    storage = MemoryStorage()
    return Dispatcher(storage=storage)


async def main():
    """
    Главная функция приложения.
    Координирует инициализацию всех компонентов и запуск бота.
    """
    # Настраиваем логирование
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Создаем бота и диспетчер
        bot = create_bot()
        dp = create_dispatcher()
        
        # Настраиваем обработку ошибок
        await setup_error_handling(dp)
        
        # Регистрируем все обработчики
        register_handlers(dp)
        
        # Настраиваем хуки жизненного цикла
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        logger.info("Запуск бота...")
        
        # Запускаем polling
        await dp.start_polling(
            bot,
            skip_updates=True,  # Пропускаем накопившиеся сообщения при перезапуске
            handle_signals=True  # Корректно обрабатываем сигналы остановки
        )
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки от пользователя")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
    finally:
        logger.info("Завершение работы бота")


if __name__ == "__main__":
    """
    Точка входа в приложение.
    Запускает главную асинхронную функцию в event loop.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка запуска: {e}")
        sys.exit(1)