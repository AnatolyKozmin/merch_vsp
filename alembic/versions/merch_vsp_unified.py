"""
Объединённая миграция для всех таблиц и изменений

Revision ID: merch_vsp_unified
Revises: 
Create Date: 2025-08-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'merch_vsp_unified'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # product_types
    op.create_table('product_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    # users
    op.create_table('users',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('registered_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    # products
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('sizes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('price', sa.String(), nullable=False),
        sa.Column('palette', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('photo', sa.String(), nullable=True),
        sa.Column('caption', sa.String(), nullable=True),
        sa.Column('material', sa.String(), nullable=True),
        sa.Column('sizes_text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['type_id'], ['product_types.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # cart
    op.create_table('cart',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('size', sa.String(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # size_setka
    op.create_table('size_setka',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('photo', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    # orders
    op.create_table('orders',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.BigInteger, index=True),
        sa.Column('username', sa.String),
        sa.Column('fio', sa.String),
        sa.Column('phone', sa.String),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    # order_items
    op.create_table('order_items',
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
    op.drop_table('size_setka')
    op.drop_table('cart')
    op.drop_table('products')
    op.drop_table('users')
    op.drop_table('product_types')
