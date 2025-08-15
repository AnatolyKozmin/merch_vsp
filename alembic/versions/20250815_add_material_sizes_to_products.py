"""add material and sizes_text fields to products

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2025-08-15
"""
from alembic import op
import sqlalchemy as sa

revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('products', sa.Column('material', sa.String(), nullable=True))
    op.add_column('products', sa.Column('sizes_text', sa.String(), nullable=True))

def downgrade():
    op.drop_column('products', 'material')
    op.drop_column('products', 'sizes_text')
