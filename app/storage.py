"""Хранение заказов в файле JSON (data/orders.json).

Форма дописывает файл, список и карточка его читают.
Внутри контейнера файл живёт, пока контейнер запущен.
"""
import json
import threading

from app.config import BASE_DIR

DATA_FILE = BASE_DIR / "data" / "orders.json"
_lock = threading.Lock()


def load_orders() -> list[dict]:
    with _lock:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def get_order(order_id: int) -> dict | None:
    return next((o for o in load_orders() if o["id"] == order_id), None)


def add_order(order: dict) -> dict:
    with _lock:
        orders = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        order["id"] = max((o["id"] for o in orders), default=0) + 1
        orders.append(order)
        DATA_FILE.write_text(json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8")
    return order
