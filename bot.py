from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, search, request, appointment, chat, admin
import asyncio
import logging
import sys
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.DEBUG)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(
        start.router,
        search.router,
        request.router,
        appointment.router,
        chat.router,
        admin.router
    )
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())