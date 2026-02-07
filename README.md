# 🤖 Instagram Automation Bot

Telegram бот для автоматизации Instagram контента на базе aiogram.

## 🎯 Возможности

- 🔍 Парсинг вирусных постов из Instagram
- 🤖 AI обработка и переписывание контента
- 🎨 Генерация каруселей через Orshot
- ✅ Система одобрения через Telegram
- 📅 Расписание публикаций
- 📊 Интеграция с Google Sheets

## 🚀 Деплой на VPS

Чтобы выгрузить бота на сервер и тестировать там:

1. **Инструкция:** [docs/DEPLOY_VPS.md](docs/DEPLOY_VPS.md) — установка Docker на VPS, выгрузка проекта, запуск.
2. **Скрипт с ПК (Windows):** отредактируй в `scripts/deploy-to-vps.ps1` переменные `$VPS_USER` и `$VPS_HOST`, затем выполни:
   ```powershell
   cd c:\Users\Admin\.cursor\instagram_bot
   .\scripts\deploy-to-vps.ps1
   ```
   Скрипт загрузит код и `.env` на сервер и запустит `docker compose up -d --build`.

---

## 📦 Установка (локально)

### 1. Клонирование и настройка окружения

```bash
cd instagram_bot
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

Заполните необходимые ключи:
- `BOT_TOKEN` - токен Telegram бота
- `OPENROUTER_API_KEY` - ключ OpenRouter
- `ORSOT_API_KEY` - ключ Orshot
- `GOOGLE_SHEETS_ID` - ID Google таблицы
- `DATABASE_URL` - URL базы данных

### 4. Настройка базы данных

```bash
# Для SQLite (по умолчанию)
python scripts/init_db.py

# Для PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
python scripts/init_db.py
```

### 5. Запуск бота

```bash
python main.py
```

## 🏗️ Структура проекта

```
instagram_bot/
├── app/
│   ├── __init__.py
│   ├── main.py              # Точка входа
│   ├── config.py            # Конфигурация
│   ├── database.py          # Настройка БД
│   │
│   ├── handlers/            # Обработчики сообщений
│   │   ├── __init__.py
│   │   ├── start.py
│   │   ├── parse.py
│   │   ├── approval.py      # Система одобрения
│   │   └── carousel.py      # Генерация каруселей
│   │
│   ├── services/            # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── instagram_parser.py
│   │   ├── ai_rewriter.py
│   │   ├── carousel_generator.py
│   │   ├── google_sheets.py
│   │   └── scheduler.py
│   │
│   ├── models/              # Модели данных
│   │   ├── __init__.py
│   │   ├── post.py
│   │   └── author.py
│   │
│   ├── utils/               # Утилиты
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── validators.py
│   │
│   └── middleware/          # Middleware
│       ├── __init__.py
│       └── error_handler.py
│
├── scripts/                 # Скрипты
│   ├── init_db.py
│   └── migrate.py
│
├── tests/                   # Тесты
│   ├── __init__.py
│   ├── test_parser.py
│   └── test_ai.py
│
├── .env.example            # Пример конфигурации
├── .env                    # Ваша конфигурация (не коммитить!)
├── requirements.txt        # Зависимости
├── README.md              # Этот файл
└── IMPLEMENTATION_PLAN.md # План реализации
```

## 🚀 Быстрый старт

1. **Создайте бота в Telegram:**
   - Напишите @BotFather
   - Создайте нового бота
   - Получите токен

2. **Настройте .env файл:**
   ```env
   BOT_TOKEN=your_telegram_bot_token
   OPENROUTER_API_KEY=your_openrouter_key
   ORSOT_API_KEY=your_orshot_key
   ```

3. **Запустите бота:**
   ```bash
   python main.py
   ```

4. **Используйте команды:**
   - `/start` - Начать работу
   - `/parse` - Запустить парсинг Instagram
   - `/stats` - Статистика

## 📚 Документация

Подробная документация доступна в:
- `IMPLEMENTATION_PLAN.md` - Пошаговый план реализации
- `AIogram_Instagram_Implementation_Guide.md` - Техническое руководство

## 🔧 Разработка

### Добавление новой функции

1. Создайте обработчик в `app/handlers/`
2. Создайте сервис в `app/services/` (если нужна бизнес-логика)
3. Добавьте роутер в `app/main.py`
4. Напишите тесты в `tests/`

### Запуск тестов

```bash
pytest tests/
```

## 📝 Лицензия

MIT

## 👤 Автор

Создано для автоматизации Instagram контента

---

## 🚀 Быстрый старт (Docker)

### 1. Клонируй репозиторий

```bash
git clone <repo_url>
cd instagram_viral_bot
```

### 2. Настрой переменные окружения

```bash
cp .env.example .env
# Отредактируй .env и добавь свои API ключи
```

### 3. Запусти через Docker Compose

```bash
docker-compose up -d
```

### 4. Проверь логи

```bash
docker-compose logs -f bot
```

### 5. Остановка

```bash
docker-compose down
```

### Разработка без Docker

```bash
# Создай виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Установи зависимости
pip install -r requirements.txt

# Запусти бота
python -m src.bot.main
```
