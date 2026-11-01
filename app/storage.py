"""Хранение заказов в базе PostgreSQL (отдельный контейнер db).

Схема повторяет ER-диаграмму из ЛР5 3 курса (сущности DataSource и Order):
  data_sources  источники заказов (Сайт ГрузоПоиск, Avito, АТИ, Telegram);
  orders        заказы на перевозку, каждый ссылается на свой источник (source_id).
Таблица называется orders, а не order, потому что ORDER зарезервированное слово SQL.

init_db() при старте приложения сама создаёт таблицы, если их ещё нет,
и заполняет справочник источников. Демо-заказов нет: после первого запуска
список заказов пустой. Данные живут в томе dbdata, поэтому не пропадают
после docker compose down и docker compose up -d.
"""
import time

import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL, SOURCE_SITE

CREATE_TABLES = """
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
"""

SOURCES = [
    (SOURCE_SITE, "http://localhost:8080"),
    ("Avito", "https://www.avito.ru"),
    ("АТИ", "https://ati.su"),
    ("Telegram", "https://t.me"),
]

INSERT = """
INSERT INTO orders (title, description, city_from, city_to, weight, volume, body_type, price,
                    payment_type, contacts, original_url, load_date, source_id)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        (SELECT id FROM data_sources WHERE name = %s))
RETURNING id
"""

SELECT = """
SELECT o.*, s.name AS source_name,
       o.parsed_at AT TIME ZONE 'Europe/Ulyanovsk' AS parsed_local
FROM orders o JOIN data_sources s ON s.id = o.source_id
"""


def connect():
    """Новое подключение к базе. Строки приходят словарями: row["city_from"]."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=3)


def init_db(attempts: int = 30) -> None:
    """Создать таблицы и справочник источников. Ждём базу до 30 секунд, если она ещё стартует."""
    if not DATABASE_URL:
        raise RuntimeError("Не задана переменная DATABASE_URL (её задаёт docker-compose.yml)")
    for attempt in range(1, attempts + 1):
        try:
            with connect() as conn:
                conn.execute(CREATE_TABLES)
                for name, url in SOURCES:
                    conn.execute(
                        "INSERT INTO data_sources (name, base_url) VALUES (%s, %s) "
                        "ON CONFLICT (name) DO NOTHING", (name, url))
            return
        except psycopg.OperationalError:
            if attempt == attempts:
                raise
            time.sleep(1)


def load_orders() -> list[dict]:
    """Все заказы с названием источника, новые сверху."""
    with connect() as conn:
        return conn.execute(SELECT + " ORDER BY o.id DESC").fetchall()


def get_order(order_id: int) -> dict | None:
    with connect() as conn:
        return conn.execute(SELECT + " WHERE o.id = %s", (order_id,)).fetchone()


def add_order(order: dict) -> dict:
    """Сохранить новый заказ. База сама выдаёт ему номер id."""
    with connect() as conn:
        row = conn.execute(INSERT, (
            order["title"], order["description"], order["city_from"], order["city_to"],
            order["weight"], order["volume"], order["body_type"], order["price"],
            order["payment_type"], order["contacts"], None, order["load_date"], order["source"],
        )).fetchone()
    order["id"] = row["id"]
    return order
