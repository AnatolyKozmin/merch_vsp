"""add size_setka table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2025-08-15
"""
from alembic import op
import sqlalchemy as sa

revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'size_setka',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('photo', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

def downgrade():
    op.drop_table('size_setka')
