"""add replies, edits, reactions

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('reply_to_id', sa.Integer(), nullable=True))
    op.add_column('messages', sa.Column('edited_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_messages_reply_to_id', 'messages', 'messages', ['reply_to_id'], ['id'], ondelete='SET NULL')

    op.create_table(
        'reactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('message_id', sa.Integer(), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('emoji', sa.String(32), nullable=False),
        sa.UniqueConstraint('message_id', 'user_id', 'emoji', name='uq_reactions'),
    )


def downgrade() -> None:
    op.drop_table('reactions')
    op.drop_constraint('fk_messages_reply_to_id', 'messages', type_='foreignkey')
    op.drop_column('messages', 'edited_at')
    op.drop_column('messages', 'reply_to_id')
