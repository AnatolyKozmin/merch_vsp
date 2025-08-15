from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSONB
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow)
    cart_items = relationship('Cart', back_populates='user')

class ProductType(Base):
    __tablename__ = 'product_types'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    products = relationship('Product', back_populates='type')

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey('product_types.id'))
    name = Column(String, nullable=False)
    sizes = Column(JSONB, nullable=False)  # список размеров
    price = Column(String, nullable=False)  # теперь строка, можно диапазон и текст
    palette = Column(JSONB, nullable=True)  # список цветов/смайликов
    photo = Column(String, nullable=True)   # ссылка на фото или file_id
    caption = Column(String, nullable=True) # подпись к фото
    type = relationship('ProductType', back_populates='products')
    cart_items = relationship('Cart', back_populates='product')

class Cart(Base):
    __tablename__ = 'cart'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    color = Column(String, nullable=True)
    size = Column(String, nullable=True)
    quantity = Column(Integer, default=1)
    user = relationship('User', back_populates='cart_items')
    product = relationship('Product', back_populates='cart_items')
