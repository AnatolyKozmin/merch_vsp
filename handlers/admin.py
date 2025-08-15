from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import AsyncSessionLocal
from database.models import Product, ProductType
import json
from dotenv import load_dotenv
load_dotenv()
import os
from sqlalchemy import select, text

router = Router()

API_TOKEN = os.getenv('TOKEN')
DATABASE_URL = os.getenv('DB_URL')
ADMIN_IDS = [int(i) for i in os.getenv('ADMIN', '').split(',') if i]

class ProductForm(StatesGroup):
    type = State()
    name = State()
    sizes = State()
    price = State()
    photo = State()
    caption = State()

class SetkaForm(StatesGroup):
    photo = State()

@router.message(Command('admin'))
async def admin_panel(message: types.Message):
    print("ADMIN CMD RECEIVED FROM:", message.from_user.id)
    if message.from_user.id not in ADMIN_IDS:
        await message.answer('Нет доступа')
        return
    await message.answer('Админ-панель\nДоступные команды:\n/add_product — добавить товар')

@router.message(Command('add_product'))
async def add_product(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer('Нет доступа')
        return
    await message.answer('Введите тип товара (например: майка, кофта, лонгслив):')
    await state.set_state(ProductForm.type)

@router.message(ProductForm.type)
async def process_type(message: types.Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.answer('Введите название товара:')
    await state.set_state(ProductForm.name)

@router.message(ProductForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Введите размеры через запятую (например: S,M,L):')
    await state.set_state(ProductForm.sizes)

@router.message(ProductForm.sizes)
async def process_sizes(message: types.Message, state: FSMContext):
    sizes = [s.strip() for s in message.text.split(',')]
    await state.update_data(sizes=sizes)
    await message.answer('Введите цену товара:')
    await state.set_state(ProductForm.price)

@router.message(ProductForm.price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer('Отправьте фотографию товара:')
    await state.set_state(ProductForm.photo)

@router.message(ProductForm.photo)
async def process_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer('Пожалуйста, отправьте фотографию товара.')
        return
    file_id = message.photo[-1].file_id
    await state.update_data(photo=file_id)
    await message.answer('Введите подпись к фото (или пропустите):')
    await state.set_state(ProductForm.caption)

@router.message(ProductForm.caption)
async def process_caption(message: types.Message, state: FSMContext):
    await state.update_data(caption=message.text)
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        result = await session.execute(ProductType.__table__.select().where(ProductType.name == data['type']))
        product_type = result.scalar_one_or_none()
        if not product_type:
            product_type = ProductType(name=data['type'])
            session.add(product_type)
            await session.commit()
            await session.refresh(product_type)
        product = Product(
            type_id=product_type.id,
            name=data['name'],
            sizes=json.dumps(data['sizes']),
            price=data['price'],
            photo=data['photo'],
            caption=data['caption']
        )
        session.add(product)
        await session.commit()
    await message.answer('Товар успешно добавлен!')
    await state.clear()

@router.message(Command('send_payment'))
async def send_payment_link(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer('Нет доступа')
        return
    payment_url = 'https://your-payment-link.com'  # здесь ваша ссылка на оплату
    from database.db import AsyncSessionLocal
    from database.models import Cart, User
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        sent_count = 0
        for user in users:
            cart_result = await session.execute(select(Cart).where(Cart.user_id == user.id))
            cart_items = cart_result.scalars().all()
            if cart_items:
                try:
                    await message.bot.send_message(user.id, f'Ваша корзина не пуста! Перейдите по ссылке для оплаты: {payment_url}')
                    sent_count += 1
                except Exception as e:
                    print(f'Не удалось отправить пользователю {user.id}: {e}')
        await message.answer(f'Рассылка завершена. Сообщение отправлено {sent_count} пользователям с корзиной.')

@router.message(Command('set_setka'))
async def set_setka(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer('Нет доступа')
        return
    await message.answer('Отправьте фото размерной сетки')
    await state.set_state(SetkaForm.photo)

@router.message(SetkaForm.photo)
async def process_setka_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer('Пришлите фото!')
        return
    file_id = message.photo[-1].file_id
    from database.db import AsyncSessionLocal
    from database.models import SizeSetka
    async with AsyncSessionLocal() as session:
        await session.execute(text('DELETE FROM size_setka'))  # всегда одна актуальная
        setka = SizeSetka(photo=file_id)
        session.add(setka)
        await session.commit()
    await message.answer('Размерная сетка обновлена!')
    await state.clear()
