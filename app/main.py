"""ГрузоПоиск: каркас приложения (лабораторная работа 3).

Здесь создаётся приложение FastAPI, подключаются статика, шаблоны
и маршруты трёх функций из папки routers. При старте приложение
подключается к базе PostgreSQL и само создаёт пустые таблицы.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import APP_NAME, APP_VERSION, BASE_DIR, ROLES
from app import storage
from app.routers import errors, orders
from app.templating import render



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Выполняется один раз при запуске: приложение само создаёт таблицы в базе."""
    storage.init_db()
    yield


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(orders.router)
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
    if not back.startswith("/"):
        back = "/"
    response = RedirectResponse(back, status_code=303)
    response.set_cookie("role", role, samesite="lax")
    return response
