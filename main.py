import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from database.db import AsyncSessionLocal
from database.models import User
from sqlalchemy import select
from dotenv import load_dotenv
import os
from handlers.products import router as products_router
from handlers.admin import router as admin_router

load_dotenv()

API_TOKEN = os.getenv('TOKEN')
DATABASE_URL = os.getenv('DB_URL')
ADMIN_IDS = [int(i) for i in os.getenv('ADMIN', '').split(',') if i]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
dp.include_router(products_router)
dp.include_router(admin_router)

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ''
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=user_id, username=username)
            session.add(user)
            await session.commit()
    text = 'Привет, здесь у тебя есть последняя попытка купить мерч Вспышки этого года'
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🛒 Корзина'), KeyboardButton(text='🛍️ Товары'), KeyboardButton(text='ℹ️ Инфо')]
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=kb)

if __name__ == '__main__':
    print("работает")
    dp.run_polling(bot)
