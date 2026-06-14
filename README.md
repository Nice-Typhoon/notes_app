# Notes App — Веб-приложение для управления заметками

Курсовой проект по дисциплине «Разработка веб-приложений».

## Стек технологий

| Слой | Технология |
|------|-----------|
| Backend | **FastAPI** (Python 3.12) |
| ORM | **SQLAlchemy 2.x** (async) + **asyncpg** |
| Валидация | **Pydantic v2** |
| База данных | **PostgreSQL 16** |
| Шаблоны | **Jinja2** (серверный рендеринг) |
| Аутентификация | **JWT** (python-jose + passlib/bcrypt) |
| Миграции | **Alembic** |
| Фоновые задачи | **asyncio** (встроенный планировщик) |

## Архитектура

Модульный монолит с выделенными логическими модулями:

```
app/
├── main.py               # FastAPI app, lifespan, маршруты
├── config.py             # Настройки (pydantic-settings)
├── database.py           # Движок, сессия, Base
├── models.py             # Все SQLAlchemy-модели
├── scheduler.py          # Асинхронный планировщик напоминаний
├── modules/
│   ├── auth/             # Регистрация, вход, JWT, зависимость get_current_user
│   ├── notes/            # CRUD заметок + поиск/фильтрация по тегам
│   ├── tags/             # Управление тегами
│   ├── reminders/        # Создание и отмена напоминаний
│   └── notifications/    # Просмотр и отметка уведомлений
├── templates/            # Jinja2-шаблоны
└── static/               # CSS
```

## Быстрый старт (Docker Compose)

```bash
# 1. Клонировать / распаковать проект
# 2. Запустить
docker compose up --build

# Приложение доступно на http://localhost:8000
```

## Локальный запуск

### 1. Зависимости

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. База данных

Запустите PostgreSQL и создайте БД:

```sql
CREATE USER notes_user WITH PASSWORD 'notes_pass';
CREATE DATABASE notes_db OWNER notes_user;
```

Или через Docker:

```bash
docker run -d --name notes-pg \
  -e POSTGRES_USER=notes_user \
  -e POSTGRES_PASSWORD=notes_pass \
  -e POSTGRES_DB=notes_db \
  -p 5432:5432 \
  postgres:16-alpine
```

### 3. Переменные окружения

```bash
cp .env.example .env
# Отредактируйте .env при необходимости
```

### 4. Запуск

```bash
uvicorn app.main:app --reload
# → http://localhost:8000
```

Таблицы создаются **автоматически** при первом запуске (SQLAlchemy `create_all`).

## Функциональность

| Модуль | Возможности |
|--------|------------|
| **Auth** | Регистрация, вход, выход, JWT-куки, защита маршрутов |
| **Notes** | Создание, просмотр, редактирование, удаление; поиск по заголовку/тексту; фильтрация по тегу |
| **Tags** | Создание и удаление тегов с цветовой меткой; привязка к заметкам (many-to-many) |
| **Reminders** | Назначение напоминания с датой/временем; отмена; просмотр статуса |
| **Notifications** | Автоматическое формирование уведомлений планировщиком; отметка как прочитанных; счётчик в навбаре |

## Планировщик уведомлений

Каждые 30 секунд (`SCHEDULER_INTERVAL_SECONDS`) фоновая asyncio-задача:

1. Ищет напоминания со статусом `pending`, у которых `remind_at ≤ now`
2. Создаёт запись в таблице `notifications`
3. Переводит напоминание в статус `fired`

Всё это происходит асинхронно и не блокирует HTTP-обработчики.

## Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|-------------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://notes_user:notes_pass@localhost:5432/notes_db` | Строка подключения |
| `SECRET_KEY` | `super-secret-key-...` | Секрет для JWT (обязательно сменить в prod) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Срок жизни токена (24 ч) |
| `SCHEDULER_INTERVAL_SECONDS` | `30` | Интервал проверки напоминаний |
