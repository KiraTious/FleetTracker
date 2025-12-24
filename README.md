# FleetTracker

Система для отслеживания технического состояния транспортных средств, учета обслуживания и построения маршрутов. Проект использует Flask, SQLAlchemy и PostgreSQL. JWT авторизация добавлена для разграничения доступа по ролям (admin, manager, driver).

## Запуск через Docker

1. Соберите образы и поднимите контейнеры:
   ```bash
   docker compose build
   docker compose up
   ```
2. Приложение поднимется на `http://localhost:5000`. Страница авторизации доступна на корневом пути и из каталога `/static/index.html`, после ввода логина и пароля происходит редирект на соответствующий кабинет (`/admin`, `/manager`, `/driver`). PostgreSQL доступен с хоста на порту `55432` (проксируется на порт `5432` внутри контейнера).
3. При старте backend применяет миграции и запускает SQL-скрипт `db_seed.sql`, который добавляет тестовые данные, если их нет.
4. Для карт создайте файл `.env` на основе `.env.example` и задайте ключ Яндекс.Карт (Routing v2 + Static Maps) в переменной
   `YANDEX_MAPS_API_KEY`. Docker Compose автоматически подхватит значение и пробросит его в сервис `yandexmaps`. Ключ можно
   выпустить в [кабинете разработчика](https://developer.tech.yandex.ru/services/), включив API «Маршруты» и Static Maps.

## Контейнеры

- **db**: PostgreSQL с данными в volume `pgdata` (Dockerfile.db).
- **backend**: Flask-приложение (Dockerfile) с зависимостями из `requirements.txt`.
- **yandexmaps**: сервис-прокси к Yandex Routing v2/Static Maps API (каталог `YandexMaps/`, порт `8081`). Для работы требуется
  переменная окружения `YANDEX_MAPS_API_KEY`, которую можно задать в файле `.env` рядом с `docker-compose.yml`.

## Переменные окружения

Основные переменные задаются в `docker-compose.yml`:
- `DATABASE_URL` — строка подключения к PostgreSQL.
- `SECRET_KEY` и `JWT_SECRET_KEY` — ключи Flask и JWT.
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` — используются entrypoint-скриптом для миграций и заполнения БД.

## Роли и пользователи по умолчанию

В БД автоматически добавляются пользователи (логин/пароль `admin`):
- Администратор: `admin` / `admin`
- Менеджер: `manager` / `admin`
- Водители: `driver1`, `driver2`, `driver3` / `admin`

## JWT авторизация

- `POST /auth/login` — принимает `username` и `password`, возвращает access_token с ролью.
- `GET /auth/me` — текущий пользователь (требуется токен).
- `GET /auth/roles/demo` — пример проверки ролей (доступно admin и manager).

Токен передается в заголовке `Authorization: Bearer <token>`.

## Миграции

Миграции Alembic лежат в каталоге `migrations/`. При старте backend автоматически запускает `flask db upgrade`.
