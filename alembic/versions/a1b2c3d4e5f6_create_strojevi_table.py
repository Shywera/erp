"""create strojevi table

Revision ID: a1b2c3d4e5f6
Revises: 90c84fcbe81a
Create Date: 2026-06-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '90c84fcbe81a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'stroj',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sifra', sa.String(length=30), nullable=False),
        sa.Column('naziv', sa.String(length=255), nullable=False),
        sa.Column('tip', sa.String(length=50), nullable=True),
        sa.Column('aktivno', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('max_format_x_mm', sa.Float(), nullable=True),
        sa.Column('max_format_y_mm', sa.Float(), nullable=True),
        sa.Column('min_format_x_mm', sa.Float(), nullable=True),
        sa.Column('min_format_y_mm', sa.Float(), nullable=True),
        sa.Column('broj_boja', sa.Integer(), nullable=True),
        sa.Column('ima_lak', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('ima_uv', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('brzina_metal_arh', sa.Integer(), nullable=True),
        sa.Column('brzina_bijeli_arh', sa.Integer(), nullable=True),
        sa.Column('brzina_arh', sa.Integer(), nullable=True),
        sa.Column('broj_osoba', sa.Integer(), nullable=True),
        sa.Column('napomena', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sifra'),
    )
    op.create_index('ix_stroj_sifra', 'stroj', ['sifra'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_stroj_sifra', table_name='stroj')
    op.drop_table('stroj')
