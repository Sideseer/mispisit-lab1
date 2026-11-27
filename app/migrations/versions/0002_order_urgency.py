"""Миграция 2 (версия 0.0.6): у заказа появляется срочность.

Новое поле urgency: «Обычный» или «Срочный». Заказам, которые были в базе
до обновления, PostgreSQL сразу ставит значение по умолчанию «Обычный».

Revision ID: 0002
Revises: 0001
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE orders "
        "ADD COLUMN urgency VARCHAR(20) NOT NULL DEFAULT 'Обычный'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE orders DROP COLUMN urgency")
