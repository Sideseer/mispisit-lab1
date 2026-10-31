"""Функции 1 и 2: создание заказа и просмотр заказов (список и карточка)."""
from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import storage
from app.config import CAN_CREATE_ORDER, ROLES, SOURCE_SITE
from app.templating import current_role, render

router = APIRouter(prefix="/orders")


@router.get("", response_class=HTMLResponse)
def orders_list(request: Request):
    """Функция 2. Просмотр: список опубликованных заказов, новые сверху."""
    orders = storage.load_orders()
    created = request.query_params.get("created")
    return render(request, "orders/list.html", {"orders": orders, "created": created})


@router.get("/new", response_class=HTMLResponse)
def order_form(request: Request):
    """Форма нового заказа. Водителю форма не открывается: отказ по роли."""
    role = current_role(request)
    if role not in CAN_CREATE_ORDER:
        return RedirectResponse(f"/access-denied?role={role}&action=create", status_code=303)
    return render(request, "orders/new.html", {"form": {}, "today": date.today().isoformat()})


@router.post("/new", response_class=HTMLResponse)
def order_create(
    request: Request,
    from_city: str = Form(""),
    to_city: str = Form(""),
    cargo: str = Form(""),
    weight: str = Form(""),
    price: str = Form(""),
    load_date: str = Form(""),
    shipper: str = Form(""),
):
    """Функция 1. Создание заказа. При ошибочных данных показывается страница отказа."""
    role = current_role(request)
    if role not in CAN_CREATE_ORDER:
        return RedirectResponse(f"/access-denied?role={role}&action=create", status_code=303)

    form = {
        "from_city": from_city.strip(), "to_city": to_city.strip(), "cargo": cargo.strip(),
        "weight": weight.strip(), "price": price.strip(), "load_date": load_date.strip(),
        "shipper": shipper.strip(),
    }
    errors = validate(form)
    if errors:
        return render(request, "access_denied.html", {
            "kind": "validation",
            "who": ROLES[role],
            "action": "Создать заказ на перевозку",
            "reasons": errors,
            "form": form,
        }, status_code=422)

    order = storage.add_order({
        "from_city": form["from_city"],
        "to_city": form["to_city"],
        "cargo": form["cargo"],
        "weight": float(form["weight"].replace(",", ".")),
        "price": int(float(form["price"].replace(",", "."))),
        "load_date": form["load_date"],
        "shipper": form["shipper"],
        "source": SOURCE_SITE,
    })
    return RedirectResponse(f"/orders?created={order['id']}", status_code=303)


@router.get("/{order_id}", response_class=HTMLResponse)
def order_card(request: Request, order_id: int):
    """Функция 2. Просмотр: карточка одного заказа целиком."""
    order = storage.get_order(order_id)
    if order is None:
        return render(request, "access_denied.html", {
            "kind": "not_found",
            "who": ROLES[current_role(request)],
            "action": f"Открыть заказ № {order_id}",
            "reasons": ["Заказа с таким номером нет в системе."],
        }, status_code=404)
    return render(request, "orders/card.html", {"order": order})


def validate(form: dict) -> list[str]:
    """Проверка формы заказа. Возвращает список причин отказа."""
    errors = []
    names = {"from_city": "Откуда", "to_city": "Куда", "cargo": "Груз", "weight": "Вес",
             "price": "Цена", "load_date": "Дата загрузки", "shipper": "Грузоотправитель"}
    for key, title in names.items():
        if not form[key]:
            errors.append(f"Не заполнено поле «{title}».")

    if form["weight"]:
        try:
            weight = float(form["weight"].replace(",", "."))
            if weight <= 0:
                errors.append("Вес груза должен быть больше нуля.")
            elif weight > 40:
                errors.append("Вес больше 40 т: такой груз не возьмёт ни один водитель на сайте.")
        except ValueError:
            errors.append("Вес нужно указать числом, например 1.5.")

    if form["price"]:
        try:
            if float(form["price"].replace(",", ".")) <= 0:
                errors.append("Цена перевозки должна быть больше нуля.")
        except ValueError:
            errors.append("Цену нужно указать числом в рублях.")

    if form["from_city"] and form["from_city"].lower() == form["to_city"].lower():
        errors.append("Город загрузки и город выгрузки совпадают.")
    return errors
