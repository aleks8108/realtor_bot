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
from aiogram.exceptions import TelegramAPIError

# Установка уровня логирования на DEBUG
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Импортируем конфигурацию и обработчики
from config import BOT_TOKEN, LOGGING_LEVEL, validate_config
from handlers import admin, request, start, calculators

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
        BotCommand(command="cancel", description="❌ Отменить текущее действие"),
        BotCommand(command="admin", description="🛠 Кабинет администратора"),
        BotCommand(command="calculators", description="📊 Калькуляторы")
    ]
    
    await bot.set_my_commands(commands)

def register_handlers(dp: Dispatcher):
    """
    Регистрирует все обработчики сообщений в диспетчере.
    Порядок регистрации важен - более специфичные обработчики должны быть первыми.
    """
    dp.include_router(admin.router)
    dp.include_router(request.router)
    dp.include_router(calculators.router)
    dp.include_router(start.router)

def setup_global_error_handler(dp: Dispatcher):
    """
    Настраивает глобальный обработчик ошибок для диспетчера.
    Перехватывает исключения и логирует их для анализа.
    """
    @dp.errors()
    async def errors_handler(event: TelegramAPIError):
        logger = logging.getLogger(__name__)
        logger.error(f"Произошла ошибка Telegram API: {event}")
        return True

async def on_startup(bot: Bot):
    """
    Выполняется при запуске бота.
    Инициализирует необходимые ресурсы и настройки.
    """
    logger = logging.getLogger(__name__)
    
    try:
        bot_info = await bot.get_me()
        logger.info(f"Бот запущен: @{bot_info.username} ({bot_info.full_name})")
        
        await setup_bot_commands(bot)
        logger.info("Команды бота настроены")
        
        from services.sheets import google_sheets_service
        test_properties = await google_sheets_service.get_all_properties()
        logger.info(f"Google Sheets подключен. Найдено {len(test_properties) if test_properties else 0} объектов")
        
        from handlers.admin import init_db
        init_db()
        
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
    from services.sheets import google_sheets_service
    await google_sheets_service.close()
    await bot.session.close()

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
            parse_mode=ParseMode.HTML,
            protect_content=False,
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
    logger = logging.getLogger(__name__)
    
    try:
        validate_config()
        
        bot = create_bot()
        dp = create_dispatcher()
        
        setup_global_error_handler(dp)
        register_handlers(dp)
        
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        logger.info("Запуск бота...")
        
        await dp.start_polling(
            bot,
            skip_updates=True,
            handle_signals=True
        )
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки от пользователя")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
    finally:
        logger.info("Завершение работы бота")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка запуска: {e}")
        sys.exit(1)
        