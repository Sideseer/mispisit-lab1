"""Шаблонизатор Jinja2 и общие данные для всех страниц (название, версия, роль)."""
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import APP_DESCRIPTION, APP_NAME, APP_VERSION, BASE_DIR, DEFAULT_ROLE, ROLES

templates = Jinja2Templates(directory=BASE_DIR / "templates")


def current_role(request: Request) -> str:
    role = request.cookies.get("role", DEFAULT_ROLE)
    return role if role in ROLES else DEFAULT_ROLE


def render(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    data = {
        "app_name": APP_NAME,
        "app_description": APP_DESCRIPTION,
        "version": APP_VERSION,
        "roles": ROLES,
        "role": current_role(request),
        "role_title": ROLES[current_role(request)],
        "path": request.url.path,
    }
    data.update(context or {})
    return templates.TemplateResponse(request, name, data, status_code=status_code)
