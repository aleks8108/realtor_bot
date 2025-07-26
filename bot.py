import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, search  # Добавьте другие импорты по необходимости

logging.basicConfig(level=logging.DEBUG)

async def main():
    logging.info("Инициализация бота...")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(search.router)
    # Другие роутеры
    logging.info("Запуск polling...")
    await dp.start_polling(bot, handle_errors=True)

if __name__ == "__main__":
    asyncio.run(main())