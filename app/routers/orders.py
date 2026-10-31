"""Функции 1 и 2: публикация заказа (FR-09) и просмотр заказов (FR-06: список и карточка).

Названия полей совпадают с ER-диаграммой ЛР5 3 курса: title, city_from, city_to,
weight, volume, body_type, price, payment_type, contacts.
"""
from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import storage
from app.config import BODY_TYPES, CAN_CREATE_ORDER, PAYMENT_TYPES, ROLES, SOURCE_SITE
from app.templating import current_role, render

router = APIRouter(prefix="/orders")

FIELDS = ["title", "description", "city_from", "city_to", "weight", "volume",
          "body_type", "price", "payment_type", "load_date", "contacts"]


def form_context(form: dict) -> dict:
    return {"form": form, "today": date.today().isoformat(),
            "body_types": BODY_TYPES, "payment_types": PAYMENT_TYPES}


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
        "weight": to_number(form["weight"]),
        "volume": to_number(form["volume"]) if form["volume"] else None,
        "body_type": form["body_type"] or None,
        "price": int(to_number(form["price"])),
        "payment_type": form["payment_type"] or None,
        "contacts": form["contacts"],
        "load_date": form["load_date"],
        "source": SOURCE_SITE,
    })
    return RedirectResponse(f"/orders?created={order['id']}", status_code=303)


@router.get("/{order_id}", response_class=HTMLResponse)
def order_card(request: Request, order_id: int):
    """Функция 2. Просмотр: карточка заказа целиком (как макет card.html 3 курса)."""
    order = storage.get_order(order_id)
    if order is None:
        return render(request, "access_denied.html", {
            "kind": "not_found",
            "who": ROLES[current_role(request)],
            "action": f"Открыть заказ № {order_id}",
            "reasons": ["Заказ не найден: заказа с таким номером нет в системе."],
        }, status_code=404)
    return render(request, "orders/card.html", {"order": order})


def to_number(text: str) -> float:
    return float(text.replace(",", ".").replace(" ", ""))


def validate(form: dict) -> list[str]:
    """Проверка формы заказа. Возвращает список причин отказа."""
    errors = []
    required = {"title": "Название груза", "city_from": "Город откуда", "city_to": "Город куда",
                "weight": "Масса", "price": "Стоимость", "load_date": "Дата загрузки",
                "contacts": "Контакты"}
    for key, name in required.items():
        if not form[key]:
            errors.append(f"Не заполнено поле «{name}».")

    if form["weight"]:
        try:
            weight = to_number(form["weight"])
            if weight <= 0:
                errors.append("Масса груза должна быть больше нуля.")
            elif weight > 40:
                errors.append("Масса больше 40 т: такой груз не возьмёт ни один водитель на сайте.")
        except ValueError:
            errors.append("Массу нужно указать числом в тоннах, например 1.5.")

    if form["volume"]:
        try:
            if to_number(form["volume"]) <= 0:
                errors.append("Объём груза должен быть больше нуля.")
        except ValueError:
            errors.append("Объём нужно указать числом в м³, например 12.")

    if form["price"]:
        try:
            if to_number(form["price"]) <= 0:
                errors.append("Стоимость перевозки должна быть больше нуля.")
        except ValueError:
            errors.append("Стоимость нужно указать числом в рублях.")

    if form["body_type"] and form["body_type"] not in BODY_TYPES:
        errors.append("Тип кузова нужно выбрать из списка.")
    if form["payment_type"] and form["payment_type"] not in PAYMENT_TYPES:
        errors.append("Способ оплаты нужно выбрать из списка.")

    if form["city_from"] and form["city_from"].lower() == form["city_to"].lower():
        errors.append("Город отправления и город прибытия совпадают.")
    return errors
