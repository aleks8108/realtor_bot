import asyncio
import logging
import sys
import os
from typing import Any, Awaitable, Callable, Dict

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.exceptions import TelegramAPIError
from redis.asyncio import Redis

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, os.getenv("LOGGING_LEVEL", "INFO").upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.getenv("LOG_FILE", "bot.log"),
    encoding='utf-8'  # Добавлено для поддержки русского текста
)
logger = logging.getLogger(__name__)

# Снижаем уровень логирования для библиотек aiogram, чтобы уменьшить шум
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

# Импортируем конфигурацию и обработчики
from config import BOT_TOKEN, validate_config, ADMIN_ID, SPREADSHEET_ID, LOG_FILE, DATABASE_FILE
from handlers import admin, request, start, calculators
from services.sheets import google_sheets_service

# Инициализация Redis для FSM
redis = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 14988)),
    password=os.getenv("REDIS_PASSWORD", None),
    db=0
)
storage = RedisStorage(redis)

async def setup_bot_commands(bot: Bot):
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
    dp.include_router(admin.router)
    dp.include_router(request.router)
    dp.include_router(calculators.router)
    dp.include_router(start.router)

def setup_global_error_handler(dp: Dispatcher):
    @dp.errors()
    async def errors_handler(event: TelegramAPIError):
        logger.error(f"Произошла ошибка Telegram API: {event}")
        return True

async def on_startup(bot: Bot):
    bot_info = await bot.get_me()  # Получаем информацию о боте
    logger.info(f"Бот запущен: @{bot_info.username} ({bot_info.full_name})")
    await setup_bot_commands(bot)
    logger.info("Команды бота настроены")
    logger.info(f"Подключение к Redis: {await redis.ping()}")  # Проверка подключения
    # Инициализация Google Sheets
    test_properties = await google_sheets_service.get_all_properties()
    logger.info(f"Google Sheets подключен. Найдено {len(test_properties) if test_properties else 0} объектов")
    from handlers.admin import init_db
    init_db()

async def on_shutdown(bot: Bot):
    logger.info("Бот остановлен")
    await google_sheets_service.close()
    await redis.close()
    await bot.session.close()

def create_bot() -> Bot:
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
    return Dispatcher(storage=storage)

async def main():
    try:
        validate_config()
        bot = create_bot()
        dp = create_dispatcher()
        setup_global_error_handler(dp)
        register_handlers(dp)
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        logger.info("Запуск бота...")
        await dp.start_polling(bot, skip_updates=True, handle_signals=True)
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