"""change user id and cart user_id to BigInteger

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-08-15
"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('users', 'id', type_=sa.BigInteger(), existing_type=sa.Integer(), nullable=False)
    op.alter_column('cart', 'user_id', type_=sa.BigInteger(), existing_type=sa.Integer(), nullable=True)

def downgrade():
    op.alter_column('users', 'id', type_=sa.Integer(), existing_type=sa.BigInteger(), nullable=False)
    op.alter_column('cart', 'user_id', type_=sa.Integer(), existing_type=sa.BigInteger(), nullable=True)
