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

 # --- Новые обработчики корзины ---



# --- Новые обработчики корзины ---
router = Router()

class CartForm(StatesGroup):
    fio = State()
    phone = State()

PRODUCTS_PAGE_SIZE = 1
CART_PAGE_SIZE = 1
AVAILABLE_SIZES = ['s', 'm', 'l', 'xl', '2xl']

@router.message(lambda msg: msg.text == '🛍️ Товары')
async def show_products(message: types.Message, state: FSMContext):
    page = 0
    user_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).offset(page * PRODUCTS_PAGE_SIZE).limit(PRODUCTS_PAGE_SIZE))
        products = result.scalars().all()
        if not products:
            await message.answer('Товары не найдены')
            return
        product = products[0]
        # Проверяем, есть ли товар в корзине
        cart_result = await session.execute(select(Cart).where(Cart.user_id == user_id, Cart.product_id == product.id))
        in_cart = cart_result.scalar_one_or_none() is not None
        builder = InlineKeyboardBuilder()
        builder.button(text='⬅️', callback_data=f'prev_{page}')
        if in_cart:
            builder.button(text='❌', callback_data=f'remove_{product.id}_{page}')
        else:
            builder.button(text='✅', callback_data=f'add_{product.id}_{page}')
        builder.button(text='➡️', callback_data=f'next_{page}')
        builder.adjust(3)
        builder.row(types.InlineKeyboardButton(text='Размерная сетка', callback_data='size_setka'))
        caption_text = f"<b>{product.name}</b>\n"
        caption_text += f"<b>Цена:</b> {product.price}\n"
        if product.caption:
            caption_text += f"<i>{product.caption}</i>\n"
        caption_text += "\n<i>Для просмотра товаров пользуйтесь стрелочками ⬅️➡️</i>"
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
    user_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        total_result = await session.execute(select(Product))
        total_products = total_result.scalars().all()
        total_count = len(total_products)
        if total_count == 0:
            await callback.answer('Товаров нет')
            return
        if page < 0:
            page = total_count - 1
        if page >= total_count:
            page = 0
        result = await session.execute(select(Product).offset(page * PRODUCTS_PAGE_SIZE).limit(PRODUCTS_PAGE_SIZE))
        products = result.scalars().all()
        product = products[0]
        cart_result = await session.execute(select(Cart).where(Cart.user_id == user_id, Cart.product_id == product.id))
        in_cart = cart_result.scalar_one_or_none() is not None
        builder = InlineKeyboardBuilder()
        builder.button(text='⬅️', callback_data=f'prev_{page}')
        if in_cart:
            builder.button(text='❌', callback_data=f'remove_{product.id}_{page}')
        else:
            builder.button(text='✅', callback_data=f'add_{product.id}_{page}')
        builder.button(text='➡️', callback_data=f'next_{page}')
        builder.adjust(3)
        builder.row(types.InlineKeyboardButton(text='Размерная сетка', callback_data='size_setka'))
        caption_text = f"<b>{product.name}</b>\n"
        caption_text += f"<b>Цена:</b> {product.price}\n"
        if product.caption:
            caption_text += f"<i>{product.caption}</i>\n"
        caption_text += "\n<i>Для просмотра товаров пользуйтесь стрелочками ⬅️➡️</i>"
        media = types.InputMediaPhoto(
            media=product.photo or 'https://via.placeholder.com/300',
            caption=caption_text,
            parse_mode='HTML'
        )
        try:
            await callback.message.edit_media(media, reply_markup=builder.as_markup())
        except Exception as e:
            from aiogram.exceptions import TelegramBadRequest
            if isinstance(e, TelegramBadRequest) and 'message is not modified' in str(e):
                pass  # Просто игнорируем, если ничего не изменилось
            else:
                raise
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith('add_'))
async def add_to_cart(callback: types.CallbackQuery, state: FSMContext):
    product_id, page = callback.data.split('_')[1:]
    user_id = callback.from_user.id
    # Просто добавляем товар в корзину без сбора данных
    async with AsyncSessionLocal() as session:
        cart_item = Cart(
            user_id=user_id,
            product_id=int(product_id),
            size=None,
            quantity=1
        )
        session.add(cart_item)
        await session.commit()
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='🛒 Корзина'), KeyboardButton(text='🛍️ Товары')]],
        resize_keyboard=True
    )
    await callback.message.answer('Товар добавлен в корзину!', reply_markup=kb)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith('size_') and c.data.endswith('_form'))
async def select_size_form(callback: types.CallbackQuery, state: FSMContext):
    _, size, _ = callback.data.split('_')
    if size not in AVAILABLE_SIZES:
        await callback.answer('Недопустимый размер!')
        return
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        cart_item = Cart(
            user_id=callback.from_user.id,
            product_id=data['product_id'],
            size=size,
            quantity=1
        )
        session.add(cart_item)
        await session.commit()
        product_result = await session.execute(select(Product).where(Product.id == data['product_id']))
        product = product_result.scalar_one_or_none()
        if product:
            add_order(
                user_id=callback.from_user.id,
                username=callback.from_user.username or '',
                product=product.name,
                size=size,
                color='',
                quantity=cart_item.quantity
            )
        await callback.message.answer(f'Товар добавлен в корзину! Размер: {size.upper()}', reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
    await callback.answer()

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
            builder.row(types.InlineKeyboardButton(text='Оформить заказ', callback_data='checkout'))
            caption_text = f"<b>{product.name}</b>\n"
            caption_text += f"<b>Размер:</b> {item.size or 'Не выбран'}\n"
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
# Оформление заказа через корзину
@router.callback_query(lambda c: c.data == 'checkout')
async def checkout_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CartForm.fio)
    await callback.message.answer('Введите ФИО для оформления заказа:')
    await callback.answer()

@router.message(CartForm.fio)
async def checkout_fio(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await state.set_state(CartForm.phone)
    await message.answer('Введите номер телефона:')

@router.message(CartForm.phone)
async def checkout_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    user_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Cart).where(Cart.user_id == user_id))
        cart_items = result.scalars().all()
        for item in cart_items:
            product_result = await session.execute(select(Product).where(Product.id == item.product_id))
            product = product_result.scalar_one_or_none()
            if product:
                add_order(
                    user_id=user_id,
                    username=message.from_user.username or '',
                    product=product.name,
                    size=item.size or '',
                    color=item.color or '',
                    quantity=item.quantity
                )
            await session.delete(item)
        await session.commit()
    await message.answer('Спасибо! Ваш заказ оформлен. Мы свяжемся с вами для подтверждения.')
    await state.clear()

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

@router.callback_query(lambda c: c.data.startswith('size_setka'))
async def show_size_setka(callback: types.CallbackQuery):
    from database.db import AsyncSessionLocal
    from database.models import SizeSetka
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(SizeSetka).order_by(SizeSetka.created_at.desc()))
        setka = result.scalars().first()
        if setka:
            kb = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text='⬅️', callback_data='prev_0'), types.InlineKeyboardButton(text='➡️', callback_data='next_0')],
                    [types.InlineKeyboardButton(text='Размерная сетка', callback_data='size_setka')]
                ]
            )
            await callback.message.edit_media(
                types.InputMediaPhoto(
                    media=setka.photo,
                    caption='<b>Сетка размеров</b>',
                    parse_mode='HTML'
                ),
                reply_markup=kb
            )
        else:
            await callback.answer('Сетка размеров не загружена')

@router.callback_query(lambda c: c.data.startswith('remove_'))
async def confirm_remove(callback: types.CallbackQuery):
    product_id, page = callback.data.split('_')[1:]
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='Да', callback_data=f'confirm_remove_{product_id}_{page}'),
             types.InlineKeyboardButton(text='Нет', callback_data=f'cancel_remove_{product_id}_{page}')]
        ]
    )
    await callback.message.answer('Вы уверены, что хотите удалить товар из корзины?', reply_markup=kb)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith('confirm_remove_'))
async def remove_from_cart(callback: types.CallbackQuery):
    product_id, page = callback.data.split('_')[2:]
    user_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        cart_result = await session.execute(select(Cart).where(Cart.user_id == user_id, Cart.product_id == int(product_id)))
        cart_item = cart_result.scalar_one_or_none()
        if cart_item:
            await session.delete(cart_item)
            await session.commit()
            # Google Sheets
            product_result = await session.execute(select(Product).where(Product.id == int(product_id)))
            product = product_result.scalar_one_or_none()
            if product:
                remove_order(
                    user_id=user_id,
                    product=product.name,
                    size=cart_item.size,
                    color=cart_item.color or ''
                )
            await callback.message.answer('Товар удалён из корзины.')
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith('cancel_remove_'))
async def cancel_remove(callback: types.CallbackQuery):
    await callback.message.answer('Удаление отменено.')
    await callback.answer()

