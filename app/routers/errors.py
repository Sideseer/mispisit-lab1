"""Функция 3. Отказ: страница, где видно, кто что пытался сделать и почему система не дала."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.config import ROLES
from app.templating import render

router = APIRouter()

ACTIONS = {
    "create": ("Создать заказ на перевозку",
               "Создавать заказы может только заказчик. Водитель ищет и смотрит готовые заказы, "
               "а публиковать свои грузы не может."),
}


@router.get("/access-denied", response_class=HTMLResponse)
def access_denied(request: Request):
    role = request.query_params.get("role", "driver")
    action = request.query_params.get("action", "create")
    title, reason = ACTIONS.get(action, ACTIONS["create"])
    return render(request, "access_denied.html", {
        "kind": "role",
        "who": ROLES.get(role, ROLES["driver"]),
        "action": title,
        "reasons": [reason],
    }, status_code=403)
