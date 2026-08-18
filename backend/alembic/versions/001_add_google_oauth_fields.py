"""add google oauth fields to farmers

Revision ID: 001
Revises: 
Create Date: 2026-08-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add google_id column
    op.add_column('farmers', sa.Column('google_id', sa.String(255), nullable=True))
    op.create_index(op.f('ix_farmers_google_id'), 'farmers', ['google_id'], unique=True)
    
    # Add auth_provider column with enum
    auth_provider_enum = sa.Enum('password', 'google', name='authprovider')
    auth_provider_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('farmers', sa.Column('auth_provider', auth_provider_enum, nullable=False, server_default='password'))
    
    # Make password_hash nullable for Google-only accounts
    op.alter_column('farmers', 'password_hash', existing_type=sa.String(255), nullable=True)


def downgrade() -> None:
    # Revert password_hash to non-nullable
    op.alter_column('farmers', 'password_hash', existing_type=sa.String(255), nullable=False)
    
    # Drop auth_provider column
    op.drop_column('farmers', 'auth_provider')
    
    # Drop google_id column
    op.drop_index(op.f('ix_farmers_google_id'), table_name='farmers')
    op.drop_column('farmers', 'google_id')
    
    # Drop enum type
    auth_provider_enum = sa.Enum('password', 'google', name='authprovider')
    auth_provider_enum.drop(op.get_bind(), checkfirst=True)