"""add separate google and openai api configuration fields

Revision ID: 005_separate_api_configs
Revises: 004_template_style
Create Date: 2026-01-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '005_separate_api_configs'
down_revision = '004_template_style'
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """
    Add separate Google and OpenAI API configuration fields to settings table.

    This allows users to configure both providers simultaneously and switch between them
    without losing configuration.

    Idempotent: checks each column before adding.
    """
    # Add Google/Gemini API configuration columns
    if not _column_exists('settings', 'google_api_base'):
        op.add_column('settings', sa.Column('google_api_base', sa.String(length=500), nullable=True))

    if not _column_exists('settings', 'google_api_key'):
        op.add_column('settings', sa.Column('google_api_key', sa.String(length=500), nullable=True))

    # Add OpenAI API configuration columns
    if not _column_exists('settings', 'openai_api_base'):
        op.add_column('settings', sa.Column('openai_api_base', sa.String(length=500), nullable=True))

    if not _column_exists('settings', 'openai_api_key'):
        op.add_column('settings', sa.Column('openai_api_key', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """
    Remove separate API configuration columns.

    Note: This will lose the separate configuration data.
    """
    op.drop_column('settings', 'openai_api_key')
    op.drop_column('settings', 'openai_api_base')
    op.drop_column('settings', 'google_api_key')
    op.drop_column('settings', 'google_api_base')
