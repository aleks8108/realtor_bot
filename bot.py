import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import search, start

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(search.router)
    dp.include_router(start.router)
    
    logging.info("Инициализация бота...")
    try:
        logging.info("Запуск polling...")
        await dp.start_polling(bot, handle_errors=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())