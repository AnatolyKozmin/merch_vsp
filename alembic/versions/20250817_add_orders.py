"""
Revision ID: 20250817_add_orders
Revises: 
Create Date: 2025-08-17
"""
revision = '20250817_add_orders'
down_revision = None
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.BigInteger, index=True),
        sa.Column('username', sa.String),
        sa.Column('fio', sa.String),
        sa.Column('phone', sa.String),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id')),
        sa.Column('product_id', sa.Integer),
        sa.Column('product_name', sa.String),
        sa.Column('size', sa.String),
        sa.Column('color', sa.String),
        sa.Column('quantity', sa.Integer),
        sa.Column('price', sa.String),
    )

def downgrade():
    op.drop_table('order_items')
    op.drop_table('orders')
