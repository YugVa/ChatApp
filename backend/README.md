# ChatApp Backend

FastAPI сервис для управления сотрудниками с аутентификацией, аудитом и импортом/экспортом Excel.

## Быстрый старт

1. Установите зависимости (рекомендуется [Poetry](https://python-poetry.org/)):

```bash
cd backend
poetry install
```

2. Создайте файл `.env` на основе `.env.example` и укажите значения:

- `SECRET_KEY` – любая длинная строка (32+ символа)
- `FERNET_KEY` – результат `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `DATABASE_URL` – например, `sqlite:///./backend/app.db`
- `ALEMBIC_DATABASE_URL` – URL для миграций (для SQLite укажите путь без префикса `./`)

3. Примените миграции:

```bash
poetry run alembic -c alembic.ini upgrade head
```

4. Запустите приложение в режиме разработки:

```bash
poetry run uvicorn app.main:app --reload
```

Приложение доступно на `http://127.0.0.1:8000`. Интерфейс доступен после входа (`/auth/login`).

## Управление пользователями

После применения миграций вручную создайте пользователя ROOT с помощью интерактивной консоли или SQL. Пример (Poetry shell):

```bash
poetry run python - <<'PY'
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User, UserRole

db = SessionLocal()
user = User(
    username="root",
    email="root@example.com",
    full_name="Root Admin",
    role=UserRole.ROOT,
    hashed_password=get_password_hash("ChangeMe123"),
)
db.add(user)
db.commit()
db.close()
PY
```

## Импорт/экспорт Excel

- Используйте файл с колонками `first_name`, `last_name`, `rank`, `hire_date`, `attestation_date`.
- Экспортируемый файл защищен паролем из `PASSWORD_EXPORT_EXCEL` (`.env`).

## Деплой

- **Gunicorn/Uvicorn**: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`.
- **Reverse proxy**: настройте Nginx/Traefik с проксированием на порт приложения.
- **Резервное копирование**: используйте `sqlite3 app.db ".backup 'backup/app_$(date +%F).db'"` или инструменты вашей СУБД.
- **Переменные окружения**: храните секреты в `.env`/секрет-менеджере. Не коммитьте `.env`.

## Тестирование

Запустить базовые тесты (пример):

```bash
poetry run pytest
```
