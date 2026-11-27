"""Функции 1 и 2: публикация заказа (FR-09) и просмотр заказов (FR-06: список и карточка).

Названия полей совпадают с ER-диаграммой ЛР5 3 курса: title, city_from, city_to,
weight, volume, body_type, price, payment_type, contacts.
"""
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import storage
from app.config import (BODY_TYPES, CAN_CREATE_ORDER, PAYMENT_TYPES, ROLES, SOURCE_SITE,
                        URGENCY_DEFAULT, URGENCY_TYPES)
from app.templating import current_role, render

router = APIRouter(prefix="/orders")

FIELDS = ["title", "description", "city_from", "city_to", "weight", "volume",
          "body_type", "price", "payment_type", "load_date", "contacts", "urgency"]

FIELD_NAMES = {
    "title": "Название груза",
    "description": "Описание",
    "city_from": "Город откуда",
    "city_to": "Город куда",
    "weight": "Масса",
    "volume": "Объём",
    "body_type": "Тип кузова",
    "price": "Стоимость",
    "payment_type": "Оплата",
    "load_date": "Дата загрузки",
    "contacts": "Контакты",
    "urgency": "Срочность",
}

# Длины текстовых полей совпадают с VARCHAR в storage.py; для TEXT взяты разумные пределы.
MAX_LEN = {
    "title": 200,
    "description": 2000,
    "city_from": 100,
    "city_to": 100,
    "contacts": 500,
}

MAX_WEIGHT = 40
MAX_VOLUME = 200
MAX_PRICE = 100_000_000
MAX_LOAD_DAYS = 365
MAX_ORDER_ID = 2_147_483_647  # верхняя граница типа INTEGER в PostgreSQL

LOCAL_TZ = ZoneInfo("Europe/Ulyanovsk")


def today():
    """Сегодняшняя дата по времени Ульяновска, как в выводе parsed_at."""
    return datetime.now(LOCAL_TZ).date()


def form_context(form: dict) -> dict:
    return {"form": form, "today": today().isoformat(),
            "body_types": BODY_TYPES, "payment_types": PAYMENT_TYPES,
            "urgency_types": URGENCY_TYPES}


@router.get("", response_class=HTMLResponse)
def orders_list(request: Request):
    """Функция 2. Просмотр: лента заказов, новые сверху."""
    orders = storage.load_orders()
    created = request.query_params.get("created")
    return render(request, "orders/list.html", {"orders": orders, "created": created})


@router.get("/new", response_class=HTMLResponse)
def order_form(request: Request):
    """Форма нового заказа. Водителю форма не открывается: отказ по роли."""
    role = current_role(request)
    if role not in CAN_CREATE_ORDER:
        return RedirectResponse(f"/access-denied?role={role}&action=create", status_code=303)
    return render(request, "orders/new.html", form_context({}))


@router.post("/new", response_class=HTMLResponse)
def order_create(
    request: Request,
    title: str = Form(""),
    description: str = Form(""),
    city_from: str = Form(""),
    city_to: str = Form(""),
    weight: str = Form(""),
    volume: str = Form(""),
    body_type: str = Form(""),
    price: str = Form(""),
    payment_type: str = Form(""),
    load_date: str = Form(""),
    contacts: str = Form(""),
    urgency: str = Form(""),
):
    """Функция 1. Публикация заказа. При ошибочных данных показывается страница отказа."""
    role = current_role(request)
    if role not in CAN_CREATE_ORDER:
        return RedirectResponse(f"/access-denied?role={role}&action=create", status_code=303)

    values = locals()
    form = {k: values[k].strip() for k in FIELDS}
    errors = validate(form)
    if errors:
        return render(request, "access_denied.html", {
            "kind": "validation",
            "who": ROLES[role],
            "action": "Опубликовать заказ на перевозку",
            "reasons": errors,
            "form": form,
        }, status_code=422)

    order = storage.add_order({
        "title": form["title"],
        "description": form["description"] or None,
        "city_from": form["city_from"],
        "city_to": form["city_to"],
        "weight": parse_number(form["weight"]),
        "volume": parse_number(form["volume"]) if form["volume"] else None,
        "body_type": form["body_type"] or None,
        "price": int(parse_number(form["price"])),
        "payment_type": form["payment_type"] or None,
        "contacts": form["contacts"],
        "load_date": form["load_date"],
        "urgency": form["urgency"] or URGENCY_DEFAULT,
        "source": SOURCE_SITE,
    })
    return RedirectResponse(f"/orders?created={order['id']}", status_code=303)


@router.get("/{order_id}", response_class=HTMLResponse)
def order_card(request: Request, order_id: str):
    """Функция 2. Просмотр: карточка заказа целиком (как макет card.html 3 курса)."""
    number = parse_order_id(order_id)
    order = storage.get_order(number) if number is not None else None
    if order is None:
        shown = order_id if len(order_id) <= 20 else order_id[:20] + "…"
        return render(request, "access_denied.html", {
            "kind": "not_found",
            "who": ROLES[current_role(request)],
            "action": f"Открыть заказ № {shown}",
            "reasons": ["Заказ не найден: заказа с таким номером нет в системе."],
        }, status_code=404)
    return render(request, "orders/card.html", {"order": order})


def parse_order_id(order_id: str) -> int | None:
    """Номер заказа должен быть целым числом из диапазона INTEGER в базе."""
    if not order_id.isascii() or not order_id.isdigit() or len(order_id) > 10:
        return None
    number = int(order_id)
    if number < 1 or number > MAX_ORDER_ID:
        return None
    return number


def to_number(text: str) -> float:
    return float(text.replace(",", ".").replace(" ", ""))


def parse_number(text: str) -> float | None:
    """Число из поля формы или None, если это не обычное конечное число."""
    try:
        value = to_number(text)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value


def validate(form: dict) -> list[str]:
    """Проверка формы заказа. Возвращает список причин отказа."""
    errors = []
    required = {"title": "Название груза", "city_from": "Город откуда", "city_to": "Город куда",
                "weight": "Масса", "price": "Стоимость", "load_date": "Дата загрузки",
                "contacts": "Контакты"}

    for key, name in FIELD_NAMES.items():
        if "\x00" in form[key]:
            errors.append(f"В поле «{name}» есть недопустимые символы.")

    for key, name in required.items():
        if not form[key]:
            errors.append(f"Не заполнено поле «{name}».")

    for key, limit in MAX_LEN.items():
        if len(form[key]) > limit:
            errors.append(
                f"Поле «{FIELD_NAMES[key]}» слишком длинное: не больше {limit} символов."
            )

    if form["weight"]:
        weight = parse_number(form["weight"])
        if weight is None:
            errors.append("Массу нужно указать числом в тоннах, например 1.5.")
        elif weight <= 0:
            errors.append("Масса груза должна быть больше нуля.")
        elif weight > MAX_WEIGHT:
            errors.append("Масса больше 40 т: такой груз не возьмёт ни один водитель на сайте.")

    if form["volume"]:
        volume = parse_number(form["volume"])
        if volume is None:
            errors.append("Объём нужно указать числом в м³, например 12.")
        elif volume <= 0:
            errors.append("Объём груза должен быть больше нуля.")
        elif volume > MAX_VOLUME:
            errors.append("Объём больше 200 м³: такой груз не поместится в кузов.")

    if form["price"]:
        price = parse_number(form["price"])
        if price is None:
            errors.append("Стоимость нужно указать числом в рублях.")
        elif price <= 0:
            errors.append("Стоимость перевозки должна быть больше нуля.")
        elif price != int(price):
            errors.append("Стоимость нужно указать целым числом в рублях.")
        elif price > MAX_PRICE:
            errors.append("Стоимость больше 100 000 000 ₽: такую сумму система не принимает.")

    if form["body_type"] and form["body_type"] not in BODY_TYPES:
        errors.append("Тип кузова нужно выбрать из списка.")
    if form["payment_type"] and form["payment_type"] not in PAYMENT_TYPES:
        errors.append("Способ оплаты нужно выбрать из списка.")
    if form["urgency"] and form["urgency"] not in URGENCY_TYPES:
        errors.append("Срочность нужно выбрать из списка: Обычный или Срочный.")

    if form["city_from"] and form["city_to"] and form["city_from"].lower() == form["city_to"].lower():
        errors.append("Город отправления и город прибытия совпадают.")

    if form["load_date"]:
        try:
            load = datetime.strptime(form["load_date"], "%Y-%m-%d").date()
        except ValueError:
            errors.append("Дату загрузки нужно указать в формате ГГГГ-ММ-ДД, например 2026-11-20.")
        else:
            current = today()
            if load < current:
                errors.append("Дата загрузки не может быть в прошлом.")
            elif load > current + timedelta(days=MAX_LOAD_DAYS):
                errors.append("Дата загрузки слишком далёкая: указывайте дату в пределах года.")
    return errors
