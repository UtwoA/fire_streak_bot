Проект: Telegram Ogonok Bot

Структура проекта готова к открытию в IDE.

Инструкция кратко:
- Cкопировать .env.example -> .env и заполнить BOT_TOKEN и DATABASE_URL
- Применить миграции: выполнить файл app/migrations/001_create_tables.sql в Postgres (pgAdmin или psql)
- Установить зависимости: pip install -r requirements.txt
- Запустить: python -m app.main
