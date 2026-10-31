# ГрузоПоиск

Информационная система-агрегатор заказов на грузоперевозки для частных водителей и малых транспортных компаний.

Репозиторий лабораторных работ по дисциплине «Методы и средства проектирования информационных систем».

## Запуск (лабораторная работа 3)

Нужен Docker (на Windows: Docker Desktop). Приложение теперь состоит из двух контейнеров:
`app` (сайт на FastAPI) и `db` (база PostgreSQL 18). Оба поднимаются одной командой.

```bash
git clone https://github.com/Sideseer/mispisit-lab1.git
cd mispisit-lab1
docker compose up -d --build
```

Открыть в браузере: http://localhost:8080

Полезные команды:

```bash
docker compose ps          # какие контейнеры запущены (db должна быть healthy)
docker compose logs app    # журнал сайта
docker compose restart app # перезапустить сайт (заказы останутся в базе)
docker compose down        # остановить и удалить контейнеры, данные базы сохранятся в volume
docker compose down -v     # остановить и удалить ещё и данные базы (снова будут 3 демо-заказа)
```

### Вариант с готовым образом из Docker Hub

Без сборки, образ `sideseer/mispisit-lab1:0.0.3` (linux/amd64 и linux/arm64) скачается сам:

```bash
docker compose -f docker-compose.image.yml up -d
```

### Настройки (.env)

Логин, пароль и имя базы задаются переменными окружения. Пример лежит в `.env.example`.
Если ничего не делать, берутся значения по умолчанию (`gruzopoisk`). Чтобы задать свои:

```bash
cp .env.example .env       # Windows: copy .env.example .env
```

Файл `.env` в git не попадает (он в `.gitignore`). Порт сайта меняется переменной `APP_PORT`.

## Лабораторная работа 3. База данных в отдельном контейнере

- Заказы хранятся в PostgreSQL 18 (образ `postgres:18`), а не в JSON-файле.
- `docker-compose.yml` описывает два сервиса: `db` и `app`. У `db` есть healthcheck (`pg_isready`),
  `app` стартует только после того, как база готова (`depends_on: condition: service_healthy`).
- Данные базы лежат в volume `db-data`, поэтому переживают `docker compose restart` и `docker compose down`.
- Сайт подключается к базе по адресу из переменной `DATABASE_URL` (хост `db`, это имя сервиса в compose).
- При старте приложение создаёт таблицу `orders` и, если она пустая, кладёт 3 демо-заказа (`app/storage.py`).
- Роль «Заказчик» переименована в «Грузоотправитель».
- У заказа появилось поле «Источник»: откуда агрегатор взял заказ (Сайт ГрузоПоиск, Avito, Telegram).
  Заказ из формы на сайте получает источник «Сайт ГрузоПоиск». Это задел под сбор заказов с внешних площадок.

Таблица `orders`:

| Поле | Тип | Что хранит |
|---|---|---|
| id | SERIAL | номер заказа, выдаёт база |
| from_city, to_city | TEXT | откуда и куда |
| cargo | TEXT | что везём |
| weight | DOUBLE PRECISION | вес, т |
| price | INTEGER | цена, ₽ |
| load_date | DATE | дата загрузки |
| shipper | TEXT | грузоотправитель |
| source | TEXT | источник заказа |
| status | TEXT | статус (Опубликован) |
| created_at | TIMESTAMPTZ | когда заказ попал в базу |

Посмотреть данные прямо в базе:

```bash
docker compose exec db psql -U gruzopoisk -d gruzopoisk -c "SELECT id, from_city, to_city, shipper, source FROM orders;"
```

### Сборка и публикация образа

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t sideseer/mispisit-lab1:0.0.3 --push .
```

### Состав репозитория

```text
docker-compose.yml            два сервиса: app (сборка из Dockerfile) и db (postgres:18), volume, healthcheck
docker-compose.image.yml      то же, но app берётся готовым образом из Docker Hub
.env.example                  пример настроек базы и порта
Dockerfile                    сборка образа сайта (python:3.14-slim, порт 8080)
requirements.txt              зависимости с версиями (fastapi, uvicorn, jinja2, psycopg)
app/
  main.py                     создание приложения, подготовка базы при старте, главная "/", роль
  config.py                   название, версия, роли, адрес базы DATABASE_URL
  storage.py                  работа с PostgreSQL: таблица, демо-заказы, чтение и запись
  templating.py               подключение Jinja2 и общие данные для всех страниц
  routers/
    orders.py                 функции 1 и 2: создание заказа, список, карточка
    errors.py                 функция 3: страница отказа /access-denied
  templates/                  страницы (base, index, orders/list, orders/new, orders/card, access_denied)
  static/style.css            оформление
```

## Лабораторная работа 2. Три главные функции и страницы

Платформа прежняя: FastAPI (Python 3.14), страницы собирает шаблонизатор Jinja2. Один контейнер, порт 8080. После запуска приложение открывается по адресу http://localhost:8080

| Функция | Кто это делает | Что происходит | Адрес |
|---|---|---|---|
| Создать заказ на перевозку | Грузоотправитель (в лабе 2 роль называлась «Заказчик») | Изменение данных | /orders/new |
| Посмотреть заказы (список и карточка) | Водитель | Просмотр | /orders, /orders/1 |
| Попытка водителя создать заказ, ошибочные данные в форме | Водитель, Заказчик | Отказ | /access-denied |

Роль выбирается переключателем в шапке (по умолчанию «Водитель»). Создавать заказы может только заказчик.

Страницы:

- `/` главная, название продукта и переходы к действиям;
- `/orders` список заказов;
- `/orders/new` форма нового заказа;
- `/orders/1` карточка одного заказа;
- `/access-denied` отказ: кто пытался, что хотел сделать и почему система не дала.

Данные сейчас лежат в файле `app/data/orders.json` внутри контейнера: форма дописывает его, список и карточка читают. После удаления контейнера новые заказы пропадают, остаются три демо-заказа.

#### Сборка образа лабы 2

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t sideseer/mispisit-lab1:0.0.2 --push .
```

Образ в Docker Hub: https://hub.docker.com/r/sideseer/mispisit-lab1 (тег `0.0.2`, платформы linux/amd64 и linux/arm64).

#### Состав репозитория (лаба 2)

```text
Dockerfile                    сборка образа (python:3.14-slim, порт 8080)
requirements.txt              зависимости с версиями
app/
  main.py                     создание приложения, главная "/", переключатель роли
  config.py                   название, версия, роли и права
  templating.py               подключение Jinja2 и общие данные для всех страниц
  storage.py                  чтение и запись заказов в JSON
  routers/
    orders.py                 функции 1 и 2: создание заказа, список, карточка
    errors.py                 функция 3: страница отказа /access-denied
  templates/
    base.html                 общий каркас: шапка с меню и ролью, подвал
    index.html                главная
    orders/list.html          список заказов
    orders/new.html           форма нового заказа
    orders/card.html          карточка заказа
    access_denied.html        отказ и ошибочные данные
  static/style.css            оформление
  data/orders.json            демо-данные (3 заказа)
```

## Лабораторная работа 1. Первая страница

Выбор платформы (FastAPI), первая страница и образ `sideseer/mispisit-lab1:0.0.1`.
