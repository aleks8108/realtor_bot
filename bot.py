# Файл: bot.py
import asyncio
import logging
import platform
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from handlers import start, search, request, chat, admin
import signal
from dotenv import load_dotenv
import os
import traceback

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загрузка переменных из .env
load_dotenv()

# Получение токена из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Токен бота не найден в переменных окружение. Проверьте файл .env.")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Регистрация роутеров
dp.include_router(start.router)
dp.include_router(search.router)
dp.include_router(request.router)
dp.include_router(chat.router)
dp.include_router(admin.router)
logger.debug("Все роутеры успешно подключены: start, search, request, chat, admin")

async def on_startup():
    logger.info("Бот запущен!")

async def on_shutdown():
    logger.info("Бот завершает работу...")
    await bot.session.close()

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Обработка сигнала прерывания только на Unix-системах
    if platform.system() != "Windows":
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(dp.stop_polling()))
    else:
        logger.warning("Обработка сигналов прерывания не поддерживается на Windows. Используйте Ctrl+C для остановки.")

    logger.info("Запуск polling...")
    await dp.start_polling(bot)
    logger.info("Polling завершён")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}\n{traceback.format_exc()}")
    finally:
        logger.info("Завершение программы")