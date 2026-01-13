# News Monitoring Server (Windows-first)

Эта папка — стартовый каркас серверной части системы мониторинга новостей из Telegram.

## Быстрый старт (Windows)

1. Установите Python 3.11+
2. Создайте виртуальное окружение:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Установите зависимости:
   ```powershell
   pip install -U pip
   pip install -e .
   ```
4. Скопируйте `.env.example` в `.env` и заполните значения.
5. Запустите компоненты:
   ```powershell
   python -m news_monitoring api
   python -m news_monitoring collector
   python -m news_monitoring bot
   ```

Альтернативно можно использовать готовые скрипты из папки `scripts/`.

## Структура

- `src/news_monitoring/api` — FastAPI (REST + WebSocket)
- `src/news_monitoring/collector` — Telethon‑ингест
- `src/news_monitoring/processor` — правила/нормализация
- `src/news_monitoring/control_bot` — Telegram‑бот управления
- `src/news_monitoring/db` — соединение и модели БД
- `src/news_monitoring/core` — настройки/логирование

## Следующие шаги

- Подключить PostgreSQL и миграции.
- Реализовать сохранение сообщений и фильтрацию.
- Добавить команды управления в control bot.
