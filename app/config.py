"""Общие настройки ГрузоПоиска."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

APP_NAME = "ГрузоПоиск"
APP_DESCRIPTION = (
    "Агрегатор заказов на грузоперевозки для частных водителей "
    "и малых транспортных компаний: грузоотправитель публикует груз, "
    "а водитель находит подходящий заказ и откликается на него"
)
APP_VERSION = "0.0.3"

# Адрес базы PostgreSQL. Берётся из переменной окружения DATABASE_URL,
# которую задаёт docker-compose.yml (значения лежат в файле .env).
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://gruzopoisk:gruzopoisk@localhost:5432/gruzopoisk"
)

# Роли системы. Водитель главная роль: он ищет и смотрит заказы.
ROLES = {
    "driver": "Водитель",
    "shipper": "Грузоотправитель",
}
DEFAULT_ROLE = "driver"

# Кто может создавать заказы
CAN_CREATE_ORDER = {"shipper"}

# Источник заказа: откуда агрегатор его взял.
# Заказ, созданный через форму на нашем сайте, получает SOURCE_SITE.
SOURCE_SITE = "Сайт ГрузоПоиск"
