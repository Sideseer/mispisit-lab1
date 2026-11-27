"""ГрузоПоиск: рабочая версия 0.0.6.

Здесь создаётся приложение FastAPI, подключаются статика, шаблоны
и маршруты трёх функций из папки routers. При старте приложение
применяет миграции Alembic (app/migrate.py): таблицы кодом больше не создаются.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import APP_NAME, APP_VERSION, BASE_DIR, ROLES
from app.migrate import upgrade_db
from app.routers import errors, notifications, orders
from app.templating import render



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Выполняется один раз при запуске: применяем новые миграции базы."""
    upgrade_db()
    yield


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(orders.router)
app.include_router(notifications.router)
app.include_router(errors.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Главная: название продукта и переходы к действиям."""
    return render(request, "index.html")


@app.post("/role")
def choose_role(role: str = Form(...), back: str = Form("/")):
    """Переключатель роли в шапке. Роль хранится в cookie, входа по паролю пока нет."""
    if role not in ROLES:
        role = "driver"
    # Только путь своего сайта: начинается с одной /, без // и переноса строки.
    if (not back.startswith("/") or back.startswith("//")
            or "\r" in back or "\n" in back or len(back) > 200):
        back = "/"
    response = RedirectResponse(back, status_code=303)
    response.set_cookie("role", role, samesite="lax")
    return response
