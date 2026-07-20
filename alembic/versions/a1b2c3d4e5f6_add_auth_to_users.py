"""add auth to users

Revision ID: a1b2c3d4e5f6
Revises: 7e2a5978acdb
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7e2a5978acdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password_hash — existing rows get a placeholder that prevents login
    # until the user re-registers. In dev this is fine; in prod you'd migrate passwords.
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=False, server_default='!'))
    op.alter_column('users', 'password_hash', server_default=None)
    op.create_unique_constraint('uq_users_name', 'users', ['name'])


def downgrade() -> None:
    op.drop_constraint('uq_users_name', 'users', type_='unique')
    op.drop_column('users', 'password_hash')
