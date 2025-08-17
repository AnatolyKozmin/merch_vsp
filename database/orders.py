from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.models import Base

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    username = Column(String)
    fio = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer)
    product_name = Column(String)
    size = Column(String)
    color = Column(String)
    quantity = Column(Integer)
    price = Column(String)
    order = relationship('Order', back_populates='items')
