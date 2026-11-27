"""Миграция 1: структура пятой работы (заказы, источники, уведомления).

Это те же таблицы, которые версии 0.0.3-0.0.5 создавали при старте сами.
На базе пятой работы они уже есть, поэтому везде стоит IF NOT EXISTS
и ON CONFLICT DO NOTHING: миграция ничего не ломает и ничего не дублирует,
Alembic только записывает в таблицу alembic_version, что шаг 0001 применён.
На пустой базе та же миграция создаёт всё с нуля.

Revision ID: 0001
Revises:
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS data_sources (
        id         SERIAL PRIMARY KEY,
        name       VARCHAR(100) NOT NULL UNIQUE,
        base_url   VARCHAR(255) NOT NULL,
        is_active  BOOLEAN NOT NULL DEFAULT TRUE
    );

    CREATE TABLE IF NOT EXISTS orders (
        id           SERIAL PRIMARY KEY,
        source_id    INTEGER NOT NULL REFERENCES data_sources (id)
                     ON DELETE RESTRICT ON UPDATE CASCADE,
        title        VARCHAR(200) NOT NULL,
        description  TEXT,
        city_from    VARCHAR(100) NOT NULL,
        city_to      VARCHAR(100) NOT NULL,
        weight       DOUBLE PRECISION NOT NULL,
        volume       DOUBLE PRECISION,
        body_type    VARCHAR(30),
        price        INTEGER NOT NULL,
        payment_type VARCHAR(50),
        contacts     TEXT NOT NULL,
        original_url VARCHAR(500),
        load_date    DATE NOT NULL,
        status       VARCHAR(30) NOT NULL DEFAULT 'Опубликован',
        parsed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS orders_city_from_idx ON orders (city_from);
    CREATE INDEX IF NOT EXISTS orders_city_to_idx ON orders (city_to);
    CREATE INDEX IF NOT EXISTS orders_weight_idx ON orders (weight);
    CREATE INDEX IF NOT EXISTS orders_price_idx ON orders (price);

    CREATE TABLE IF NOT EXISTS notifications (
        id          SERIAL PRIMARY KEY,
        order_id    INTEGER NOT NULL REFERENCES orders (id)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
        message     TEXT NOT NULL,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        status      VARCHAR(30) NOT NULL DEFAULT 'новое'
    );

    INSERT INTO data_sources (name, base_url) VALUES
        ('Сайт ГрузоПоиск', 'http://localhost:8080'),
        ('Avito', 'https://www.avito.ru'),
        ('АТИ', 'https://ati.su'),
        ('Telegram', 'https://t.me')
    ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notifications, orders, data_sources")
