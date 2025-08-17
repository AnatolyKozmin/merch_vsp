import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from database.db import AsyncSessionLocal
from database.models import User
from database.orders import Order, OrderItem
from sqlalchemy import select
from aiogram.utils.markdown import hbold, hitalic, hcode
@dp.message(Command('get_nahui'))
async def get_nahui(message: types.Message):
    # Только для админов
    if message.from_user.id not in ADMIN_IDS:
        await message.answer('Нет доступа')
        return
    async with AsyncSessionLocal() as session:
        # Получаем все товары с заказами
        result = await session.execute(select(OrderItem.product_name).distinct())
        product_names = [row[0] for row in result.fetchall()]
        if not product_names:
            await message.answer('Нет заказов.')
            return
        messages = []
        for product_name in product_names:
            # Для каждого товара собираем список заказчиков
            result = await session.execute(
                select(OrderItem, Order)
                .join(Order, OrderItem.order_id == Order.id)
                .where(OrderItem.product_name == product_name)
                .order_by(OrderItem.size, Order.created_at)
            )
            rows = result.fetchall()
            if not rows:
                continue
            text = f"{hbold(product_name)}:\n"
            for idx, (item, order) in enumerate(rows, 1):
                username = f"@{order.username}" if order.username else hitalic('без username')
                size = item.size or hitalic('без размера')
                text += f"{idx}. {username}, {hcode(size)}\n"
            messages.append(text)
        # Отправляем по частям, если слишком длинно
        max_len = 3500
        buf = ''
        for part in messages:
            if len(buf) + len(part) > max_len:
                await message.answer(buf, parse_mode='HTML')
                buf = ''
            buf += part + '\n'
        if buf:
            await message.answer(buf, parse_mode='HTML')
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
    text = (
        'ℹ️ <b>Инфо</b>\n\n'
        'В этом чат-боте вы можете сделать <b>предзаказ</b> на мерч фестиваля «Вспышка».\n'
        'Добавив товар в корзину, вы оформляете предзаказ, после чего в течение недели вам придет ссылка на оплату.\n\n'
        'Для просмотра товаров рекомендуем нажать на кнопку <b>Товары</b> и воспользоваться стрелочками для перелистывания.\n\n'
        'Вопрос <b>доставки</b> будет решаться в индивидуальном порядке: либо самовывоз, либо оформление через Яндекс.\n\n'
        'По вопросам работы бота обращаться к @yanejettt\n'
        'По вопросам заказа обращаться к @shamonova_a'
    )
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🛒 Корзина'), KeyboardButton(text='🛍️ Товары'), KeyboardButton(text='Посмотреть корзину')]
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=kb, parse_mode='HTML')

if __name__ == '__main__':
    print("работает")
    dp.run_polling(bot)
