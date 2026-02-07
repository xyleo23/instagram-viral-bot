# 📁 Структура проекта

```
instagram_bot/
│
├── 📄 README.md                    # Основная документация
├── 📄 IMPLEMENTATION_PLAN.md        # Пошаговый план реализации
├── 📄 QUICK_START.md                # Быстрый старт
├── 📄 PROJECT_STRUCTURE.md          # Этот файл
├── 📄 requirements.txt              # Зависимости Python
├── 📄 .env.example                  # Пример конфигурации
├── 📄 .gitignore                    # Игнорируемые файлы
│
├── 📁 app/                          # Основное приложение
│   ├── __init__.py
│   ├── main.py                      # 🚀 Точка входа
│   ├── config.py                    # ⚙️ Конфигурация
│   │
│   ├── 📁 handlers/                 # Обработчики сообщений
│   │   ├── __init__.py
│   │   ├── start.py                 # /start, /help
│   │   ├── parse.py                 # /parse - парсинг Instagram
│   │   ├── approval.py              # Система одобрения постов
│   │   └── carousel.py              # Генерация каруселей
│   │
│   ├── 📁 services/                 # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── instagram_parser.py     # 🔍 Парсинг Instagram
│   │   ├── ai_rewriter.py          # 🤖 AI обработка
│   │   ├── carousel_generator.py   # 🎨 Генерация каруселей
│   │   ├── scheduler.py             # 📅 Расписание задач
│   │   └── google_sheets.py         # 📊 Google Sheets (TODO)
│   │
│   ├── 📁 models/                   # Модели данных
│   │   ├── __init__.py
│   │   ├── post.py                  # Модель поста
│   │   └── author.py                # Модель автора (TODO)
│   │
│   ├── 📁 utils/                    # Утилиты
│   │   ├── __init__.py
│   │   ├── logger.py                # 📝 Логирование
│   │   └── validators.py            # ✅ Валидация (TODO)
│   │
│   └── 📁 middleware/               # Middleware
│       ├── __init__.py
│       └── error_handler.py        # 🛡️ Обработка ошибок
│
├── 📁 scripts/                      # Вспомогательные скрипты
│   ├── init_db.py                   # Инициализация БД
│   └── migrate.py                   # Миграции (TODO)
│
├── 📁 tests/                        # Тесты
│   ├── __init__.py
│   ├── test_parser.py               # Тесты парсера (TODO)
│   ├── test_ai.py                  # Тесты AI (TODO)
│   └── test_handlers.py            # Тесты handlers (TODO)
│
└── 📁 logs/                        # Логи (создается автоматически)
    └── bot.log
```

## 📋 Описание компонентов

### 🚀 Основные файлы

- **`main.py`** - Точка входа, запускает бота и настраивает все компоненты
- **`config.py`** - Централизованная конфигурация через Pydantic Settings
- **`logger.py`** - Настройка логирования (Winston-like)

### 🔍 Handlers (Обработчики)

- **`start.py`** - Команды `/start` и `/help`
- **`parse.py`** - Команда `/parse` для запуска парсинга
- **`approval.py`** - Callback handlers для одобрения/отклонения постов
- **`carousel.py`** - Генерация каруселей по запросу

### ⚙️ Services (Сервисы)

- **`instagram_parser.py`** - Парсинг публичного Instagram API
- **`ai_rewriter.py`** - Интеграция с OpenRouter для AI обработки
- **`carousel_generator.py`** - Генерация слайдов через Orshot API
- **`scheduler.py`** - Настройка расписания задач (APScheduler)

### 📊 Models (Модели)

- **`post.py`** - Pydantic модели для постов
- Используются для валидации и сериализации данных

### 🛠️ Utils (Утилиты)

- **`logger.py`** - Централизованное логирование
- **`validators.py`** - Валидация данных (TODO)

### 🛡️ Middleware

- **`error_handler.py`** - Глобальная обработка ошибок

## 🔄 Поток данных

```
1. Парсинг Instagram
   └─> instagram_parser.py
       └─> Фильтрация постов
           └─> Сохранение в БД

2. AI обработка
   └─> ai_rewriter.py
       └─> OpenRouter API
           └─> Парсинг ответа
               └─> Обновление БД

3. Система одобрения
   └─> approval.py (handlers)
       └─> Callback от пользователя
           └─> Обновление статуса в БД

4. Генерация карусели
   └─> carousel.py (handlers)
       └─> carousel_generator.py
           └─> Orshot API
               └─> Создание медиа-группы
                   └─> Отправка в Telegram

5. Расписание
   └─> scheduler.py
       └─> Автоматический парсинг
       └─> Автоматическая публикация
```

## 📝 TODO (Что нужно доделать)

- [ ] База данных (SQLAlchemy модели и миграции)
- [ ] Полная интеграция всех сервисов
- [ ] Google Sheets интеграция
- [ ] Google Drive интеграция
- [ ] Публикация в Instagram
- [ ] Unit тесты
- [ ] Интеграционные тесты
- [ ] Документация API

## 🎯 Следующие шаги

1. Настройте `.env` файл
2. Установите зависимости
3. Запустите `scripts/init_db.py`
4. Запустите бота через `python -m app.main`
5. Начните реализацию по плану из `IMPLEMENTATION_PLAN.md`
