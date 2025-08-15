from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import AsyncSessionLocal
from database.models import Product, Cart
from sqlalchemy import select
from aiogram.filters import Command
from aiogram.types import InputMediaPhoto
from google_sheets import add_order, remove_order

router = Router()

class CartForm(StatesGroup):
    fio = State()
    phone = State()
    size = State()

PRODUCTS_PAGE_SIZE = 1
CART_PAGE_SIZE = 1

@router.message(lambda msg: msg.text == '🛍️ Товары')
async def show_products(message: types.Message, state: FSMContext):
    page = 0
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).offset(page * PRODUCTS_PAGE_SIZE).limit(PRODUCTS_PAGE_SIZE))
        products = result.scalars().all()
        if not products:
            await message.answer('Товары не найдены')
            return
        product = products[0]
        builder = InlineKeyboardBuilder()
        builder.button(text='⬅️', callback_data=f'prev_{page}')
        builder.button(text='➕', callback_data=f'add_{product.id}_{page}')
        builder.button(text='➡️', callback_data=f'next_{page}')
        builder.adjust(3)
        caption_text = f"<b>{product.name}</b>\n"
        caption_text += f"<b>Цена:</b> {product.price}\n"
        if product.caption:
            caption_text += f"<i>{product.caption}</i>"
        await message.answer_photo(
            photo=product.photo or 'https://via.placeholder.com/300',
            caption=caption_text,
            reply_markup=builder.as_markup(),
            parse_mode='HTML'
        )

@router.callback_query(lambda c: c.data.startswith('prev_') or c.data.startswith('next_'))
async def paginate_products(callback: types.CallbackQuery, state: FSMContext):
    if callback.data.startswith('prev_'):
        page = max(0, int(callback.data.split('_')[1]) - 1)
    else:
        page = int(callback.data.split('_')[1]) + 1
    async with AsyncSessionLocal() as session:
        total_result = await session.execute(select(Product))
        total_products = total_result.scalars().all()
        total_count = len(total_products)
        if total_count == 0:
            await callback.answer('Товаров нет')
            return
        # Циклическая пагинация
        if page < 0:
            page = total_count - 1
        if page >= total_count:
            page = 0
        result = await session.execute(select(Product).offset(page * PRODUCTS_PAGE_SIZE).limit(PRODUCTS_PAGE_SIZE))
        products = result.scalars().all()
        product = products[0]
        builder = InlineKeyboardBuilder()
        builder.button(text='⬅️', callback_data=f'prev_{page}')
        builder.button(text='➕', callback_data=f'add_{product.id}_{page}')
        builder.button(text='➡️', callback_data=f'next_{page}')
        builder.adjust(3)
        caption_text = f"<b>{product.name}</b>\n"
        caption_text += f"<b>Цена:</b> {product.price}\n"
        if product.caption:
            caption_text += f"<i>{product.caption}</i>"
        media = types.InputMediaPhoto(
            media=product.photo or 'https://via.placeholder.com/300',
            caption=caption_text,
            parse_mode='HTML'
        )
        await callback.message.edit_media(media, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith('add_'))
async def add_to_cart(callback: types.CallbackQuery, state: FSMContext):
    product_id, page = callback.data.split('_')[1:]
    await state.set_state(CartForm.fio)
    await state.update_data(product_id=int(product_id), page=int(page))
    await callback.message.answer('Введите ФИО:')
    await callback.answer()

@router.message(CartForm.fio)
async def process_fio(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await message.answer('Введите номер телефона:')
    await state.set_state(CartForm.phone)

@router.message(CartForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer('Выберите размер одежды (S/M/L):')
    await state.set_state(CartForm.size)

@router.message(CartForm.size)
async def process_size(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        cart_item = Cart(
            user_id=message.from_user.id,
            product_id=data['product_id'],
            size=message.text,
            # color можно добавить через отдельный callback
        )
        session.add(cart_item)
        await session.commit()
        # Получаем данные о товаре для записи в Google Sheets
        product_result = await session.execute(select(Product).where(Product.id == data['product_id']))
        product = product_result.scalar_one_or_none()
        if product:
            add_order(
                user_id=message.from_user.id,
                username=message.from_user.username or '',
                product=product.name,
                size=message.text,
                color=cart_item.color or '',
                quantity=cart_item.quantity
            )
    await message.answer('Товар добавлен в корзину!')
    await state.clear()

@router.message(lambda msg: msg.text == '🛒 Корзина')
async def show_cart(message: types.Message, state: FSMContext):
    page = 0
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Cart).where(Cart.user_id == message.from_user.id).offset(page * CART_PAGE_SIZE).limit(CART_PAGE_SIZE))
        cart_items = result.scalars().all()
        if not cart_items:
            await message.answer('Ваша корзина пуста.')
            return
        item = cart_items[0]
        product_result = await session.execute(select(Product).where(Product.id == item.product_id))
        product = product_result.scalar_one_or_none()
        if product:
            builder = InlineKeyboardBuilder()
            builder.button(text='⬅️', callback_data=f'cart_prev_{page}')
            builder.button(text='🗑️ Удалить', callback_data=f'cart_del_{item.id}_{page}')
            builder.button(text='➡️', callback_data=f'cart_next_{page}')
            builder.adjust(3)
            caption_text = f"<b>{product.name}</b>\n"
            caption_text += f"<b>Размер:</b> {item.size}\n"
            caption_text += f"<b>Цвет:</b> {item.color or 'Не выбран'}\n"
            caption_text += f"<b>Количество:</b> {item.quantity}\n"
            caption_text += f"<b>Цена:</b> {product.price}\n"
            if product.caption:
                caption_text += f"<i>{product.caption}</i>"
            await message.answer_photo(
                photo=product.photo or 'https://via.placeholder.com/300',
                caption=caption_text,
                reply_markup=builder.as_markup(),
                parse_mode='HTML'
            )

@router.callback_query(lambda c: c.data.startswith('cart_prev_') or c.data.startswith('cart_next_'))
async def paginate_cart(callback: types.CallbackQuery, state: FSMContext):
    if callback.data.startswith('cart_prev_'):
        page = max(0, int(callback.data.split('_')[2]) - 1)
    else:
        page = int(callback.data.split('_')[2]) + 1
    async with AsyncSessionLocal() as session:
        total_result = await session.execute(select(Cart).where(Cart.user_id == callback.from_user.id))
        total_items = total_result.scalars().all()
        total_count = len(total_items)
        if total_count == 0:
            await callback.answer('Корзина пуста')
            return
        # Циклическая пагинация
        if page < 0:
            page = total_count - 1
        if page >= total_count:
            page = 0
        item = total_items[page]
        product_result = await session.execute(select(Product).where(Product.id == item.product_id))
        product = product_result.scalar_one_or_none()
        if product:
            builder = InlineKeyboardBuilder()
            builder.button(text='⬅️', callback_data=f'cart_prev_{page}')
            builder.button(text='🗑️ Удалить', callback_data=f'cart_del_{item.id}_{page}')
            builder.button(text='➡️', callback_data=f'cart_next_{page}')
            builder.adjust(3)
            caption_text = f"<b>{product.name}</b>\n"
            caption_text += f"<b>Размер:</b> {item.size}\n"
            caption_text += f"<b>Цвет:</b> {item.color or 'Не выбран'}\n"
            caption_text += f"<b>Количество:</b> {item.quantity}\n"
            caption_text += f"<b>Цена:</b> {product.price}\n"
            if product.caption:
                caption_text += f"<i>{product.caption}</i>"
            media = types.InputMediaPhoto(
                media=product.photo or 'https://via.placeholder.com/300',
                caption=caption_text,
                parse_mode='HTML'
            )
            await callback.message.edit_media(media, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith('cart_del_'))
async def cart_del(callback: types.CallbackQuery, state: FSMContext):
    cart_id, page = callback.data.split('_')[2:]
    async with AsyncSessionLocal() as session:
        cart_item = await session.get(Cart, int(cart_id))
        if cart_item:
            # Получаем данные о товаре для удаления из Google Sheets
            product_result = await session.execute(select(Product).where(Product.id == cart_item.product_id))
            product = product_result.scalar_one_or_none()
            if product:
                remove_order(
                    user_id=cart_item.user_id,
                    product=product.name,
                    size=cart_item.size,
                    color=cart_item.color or ''
                )
            await session.delete(cart_item)
            await session.commit()
            await callback.message.answer('Товар удалён из корзины.')
    await show_cart(callback.message, state)
    await callback.answer()
