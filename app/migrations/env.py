"""Настройка Alembic: к какой базе подключаться при применении миграций."""
from alembic import context
from sqlalchemy import create_engine

url = context.config.get_main_option("sqlalchemy.url")
engine = create_engine(url)

with engine.connect() as connection:
    context.configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()
engine.dispose()
