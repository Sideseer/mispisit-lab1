"""Хранение заказов в базе PostgreSQL (отдельный контейнер db).

Библиотека psycopg 3 подключается к базе по адресу DATABASE_URL.
init_db() при старте приложения создаёт таблицу orders и, если она
пустая, кладёт туда 3 демо-заказа. Данные живут в volume базы,
поэтому не пропадают после перезапуска контейнеров.
"""
import time

import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    id         SERIAL PRIMARY KEY,
    from_city  TEXT NOT NULL,
    to_city    TEXT NOT NULL,
    cargo      TEXT NOT NULL,
    weight     DOUBLE PRECISION NOT NULL,
    price      INTEGER NOT NULL,
    load_date  DATE NOT NULL,
    shipper    TEXT NOT NULL,
    source     TEXT NOT NULL DEFAULT 'Сайт ГрузоПоиск',
    status     TEXT NOT NULL DEFAULT 'Опубликован',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

DEMO_ORDERS = [
    ("Ульяновск", "Самара", "Мебель для офиса, 12 коробок", 1.2, 9500,
     "2026-11-02", "ООО «СтройМебель»", "Сайт ГрузоПоиск"),
    ("Казань", "Ульяновск", "Стройматериалы на поддонах", 5, 18000,
     "2026-11-04", "ИП Сафин Р.М.", "Avito"),
    ("Димитровград", "Москва", "Автозапчасти", 3.5, 42000,
     "2026-11-06", "ООО «ДимАвтоДеталь»", "Telegram"),
]

INSERT = """
INSERT INTO orders (from_city, to_city, cargo, weight, price, load_date, shipper, source)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
RETURNING id
"""


def connect():
    """Новое подключение к базе. Строки приходят словарями: row["from_city"]."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=3)


def init_db(attempts: int = 30) -> None:
    """Создать таблицу и демо-заказы. Ждём базу до 30 секунд, если она ещё стартует."""
    for attempt in range(1, attempts + 1):
        try:
            with connect() as conn:
                conn.execute(CREATE_TABLE)
                count = conn.execute("SELECT count(*) AS n FROM orders").fetchone()["n"]
                if count == 0:
                    for order in DEMO_ORDERS:
                        conn.execute(INSERT, order)
            return
        except psycopg.OperationalError:
            if attempt == attempts:
                raise
            time.sleep(1)


def load_orders() -> list[dict]:
    """Все заказы, новые сверху."""
    with connect() as conn:
        return conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()


def get_order(order_id: int) -> dict | None:
    with connect() as conn:
        return conn.execute("SELECT * FROM orders WHERE id = %s", (order_id,)).fetchone()


def add_order(order: dict) -> dict:
    """Сохранить новый заказ. База сама выдаёт ему номер id."""
    with connect() as conn:
        row = conn.execute(INSERT, (
            order["from_city"], order["to_city"], order["cargo"], order["weight"],
            order["price"], order["load_date"], order["shipper"], order["source"],
        )).fetchone()
    order["id"] = row["id"]
    return order
