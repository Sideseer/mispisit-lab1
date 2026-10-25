"""ГрузоПоиск: первая страница (лабораторная работа 1)."""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

APP_NAME = "ГрузоПоиск"
APP_DESCRIPTION = (
    "Агрегатор заказов на грузоперевозки для частных водителей "
    "и малых транспортных компаний: заказчик публикует груз, "
    "а водитель находит подходящий заказ и откликается на него"
)
APP_VERSION = "0.0.1"
APP_STATUS = "Разработка продолжается"

app = FastAPI(title=APP_NAME, version=APP_VERSION)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "name": APP_NAME,
            "description": APP_DESCRIPTION,
            "version": APP_VERSION,
            "status": APP_STATUS,
        },
    )
