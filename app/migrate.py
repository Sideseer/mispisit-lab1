"""Миграции базы при запуске приложения (лабораторная работа 6).

Структуру базы теперь меняет не код приложения, а миграции Alembic из папки
app/migrations/versions. Каждая миграция это один записанный шаг изменения базы.
Alembic хранит номер последнего применённого шага в таблице alembic_version
и при запуске применяет только те шаги, которых в базе ещё нет.
Преподавателю не нужно выполнять отдельных команд: всё делает upgrade_db().
"""
import time

from alembic import command
from alembic.config import Config
from sqlalchemy.exc import OperationalError

from app.config import BASE_DIR, DATABASE_URL


def sqlalchemy_url() -> str:
    """Alembic работает через SQLAlchemy, ему нужен адрес вида postgresql+psycopg://."""
    return DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)


def upgrade_db(attempts: int = 30) -> None:
    """Применить все новые миграции. Ждём базу до 30 секунд, если она ещё стартует."""
    if not DATABASE_URL:
        raise RuntimeError("Не задана переменная DATABASE_URL (её задаёт docker-compose.yml)")
    config = Config()
    config.set_main_option("script_location", str(BASE_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", sqlalchemy_url())
    for attempt in range(1, attempts + 1):
        try:
            command.upgrade(config, "head")
            return
        except OperationalError:
            if attempt == attempts:
                raise
            time.sleep(1)
