# ГрузоПоиск

Информационная система-агрегатор заказов на грузоперевозки для частных водителей и малых транспортных компаний.

Репозиторий лабораторных работ по дисциплине «Методы и средства проектирования информационных систем».

## Лабораторная работа 1. Первая страница

Платформа: фреймворк FastAPI (Python 3.14). Страницу отдаёт FastAPI, HTML собирается шаблонизатором Jinja2.

Образ в Docker Hub: https://hub.docker.com/r/sideseer/mispisit-lab1

Образ собран под две платформы (linux/amd64 и linux/arm64) в одном теге `0.0.1`.

### Запуск

```bash
docker pull sideseer/mispisit-lab1:0.0.1
docker run --rm -p 8080:8080 sideseer/mispisit-lab1:0.0.1
```

После запуска страница открывается по адресу http://localhost:8080

### Сборка и публикация образа

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t sideseer/mispisit-lab1:0.0.1 --push .
```

### Состав репозитория

```text
Dockerfile               сборка образа (python:3.14-slim, порт 8080)
requirements.txt         зависимости с версиями
app/main.py              приложение FastAPI, маршрут "/"
app/templates/index.html шаблон первой страницы (Jinja2)
app/static/style.css     оформление страницы
```
