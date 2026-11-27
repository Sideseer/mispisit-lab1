"""Хранение заказов в базе PostgreSQL (отдельный контейнер db).

Схема повторяет ER-диаграмму из ЛР5 3 курса (сущности DataSource и Order):
  data_sources  источники заказов (Сайт ГрузоПоиск, Avito, АТИ, Telegram);
  orders        заказы на перевозку, каждый ссылается на свой источник (source_id).
  notifications уведомления для водителя о новом заказе (лабораторная работа 5).
У заказа с версии 0.0.6 есть поле urgency (срочность: Обычный или Срочный).
Таблица называется orders, а не order, потому что ORDER зарезервированное слово SQL.

С версии 0.0.6 таблицы создаёт не этот файл, а миграции Alembic
(папка app/migrations, запуск при старте в app/migrate.py). Здесь только
чтение и запись данных. Демо-заказов нет: после первого запуска
список заказов пустой. Данные живут в томе dbdata, поэтому не пропадают
после docker compose down и docker compose up -d.
"""
import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL

INSERT = """
INSERT INTO orders (title, description, city_from, city_to, weight, volume, body_type, price,
                    payment_type, contacts, original_url, load_date, urgency, source_id)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
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


def load_orders() -> list[dict]:
    """Все заказы с названием источника, новые сверху."""
    with connect() as conn:
        return conn.execute(SELECT + " ORDER BY o.id DESC").fetchall()


def get_order(order_id: int) -> dict | None:
    with connect() as conn:
        return conn.execute(SELECT + " WHERE o.id = %s", (order_id,)).fetchone()


def add_order(order: dict) -> dict:
    """Сохранить новый заказ. База сама выдаёт ему номер id.

    Вместе с заказом в той же транзакции создаётся уведомление для водителя.
    Если публикация не удалась, уведомления не будет.
    """
    with connect() as conn:
        row = conn.execute(INSERT, (
            order["title"], order["description"], order["city_from"], order["city_to"],
            order["weight"], order["volume"], order["body_type"], order["price"],
            order["payment_type"], order["contacts"], None, order["load_date"], order["urgency"],
            order["source"],
        )).fetchone()
        order["id"] = row["id"]
        message = (
            f"Новый заказ № {order['id']}: {order['city_from']} → {order['city_to']}, "
            f"{order['weight']:g} т"
        )
        conn.execute(
            "INSERT INTO notifications (order_id, message, status) VALUES (%s, %s, %s)",
            (order["id"], message, "новое"),
        )
    return order


def load_notifications() -> list[dict]:
    """Все уведомления, новые сверху. Время показано по Ульяновску."""
    with connect() as conn:
        return conn.execute(
            "SELECT n.*, n.created_at AT TIME ZONE 'Europe/Ulyanovsk' AS created_local "
            "FROM notifications n ORDER BY n.id DESC"
        ).fetchall()


def count_unread() -> int:
    """Сколько уведомлений ещё со статусом «новое»."""
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM notifications WHERE status = %s", ("новое",)
        ).fetchone()
    return row["n"]


def get_notification(note_id: int) -> dict | None:
    with connect() as conn:
        return conn.execute(
            "SELECT n.*, n.created_at AT TIME ZONE 'Europe/Ulyanovsk' AS created_local "
            "FROM notifications n WHERE n.id = %s", (note_id,)
        ).fetchone()


def mark_notification_read(note_id: int) -> dict | None:
    """Пометить уведомление прочитанным. Если его нет, вернуть None."""
    with connect() as conn:
        row = conn.execute(
            "UPDATE notifications SET status = %s WHERE id = %s RETURNING id",
            ("прочитано", note_id),
        ).fetchone()
    return row
