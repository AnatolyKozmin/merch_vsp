"""add photo and caption fields to products

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-08-15
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('products', sa.Column('photo', sa.String(), nullable=True))
    op.add_column('products', sa.Column('caption', sa.String(), nullable=True))

def downgrade():
    op.drop_column('products', 'photo')
    op.drop_column('products', 'caption')
