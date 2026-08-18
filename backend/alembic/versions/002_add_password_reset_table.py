"""add password reset table

Revision ID: 002
Revises: 001
Create Date: 2026-08-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'password_resets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('otp_hash', sa.String(255), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('max_attempts', sa.Integer(), nullable=False, default=5),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_resets_email'), 'password_resets', ['email'], unique=False)
    op.create_index(op.f('ix_password_resets_expires_at'), 'password_resets', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_password_resets_expires_at'), table_name='password_resets')
    op.drop_index(op.f('ix_password_resets_email'), table_name='password_resets')
    op.drop_table('password_resets')