"""change price field to string in products

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-08-15
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('products', 'price', type_=sa.String(), existing_type=sa.Float(), nullable=False)

def downgrade():
    op.alter_column('products', 'price', type_=sa.Float(), existing_type=sa.String(), nullable=False)
