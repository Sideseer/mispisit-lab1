"""Уведомления водителя о новом заказе (лабораторная работа 5).

Сообщение появляется только после успешной публикации заказа.
Ошибочная форма уведомление не создаёт. Список до первого действия пустой.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import storage
from app.config import ROLES
from app.templating import current_role, render

router = APIRouter(prefix="/notifications")

MAX_NOTE_ID = 2_147_483_647


def parse_note_id(note_id: str) -> int | None:
    if not note_id.isascii() or not note_id.isdigit() or len(note_id) > 10:
        return None
    number = int(note_id)
    if number < 1 or number > MAX_NOTE_ID:
        return None
    return number


@router.get("", response_class=HTMLResponse)
def notifications_list(request: Request):
    """Список уведомлений: текст, время, статус и ссылка на заказ."""
    notes = storage.load_notifications()
    return render(request, "notifications/list.html", {"notifications": notes})


@router.post("/{note_id}/read")
def mark_read(request: Request, note_id: str):
    """Кнопка «Прочитано»: статус меняется с «новое» на «прочитано»."""
    number = parse_note_id(note_id)
    note = storage.get_notification(number) if number is not None else None
    if note is None:
        shown = note_id if len(note_id) <= 20 else note_id[:20] + "…"
        return render(request, "access_denied.html", {
            "kind": "not_found",
            "who": ROLES[current_role(request)],
            "action": f"Отметить уведомление № {shown} как прочитанное",
            "reasons": ["Уведомление не найдено: записи с таким номером нет в системе."],
        }, status_code=404)
    storage.mark_notification_read(number)
    return RedirectResponse("/notifications", status_code=303)
