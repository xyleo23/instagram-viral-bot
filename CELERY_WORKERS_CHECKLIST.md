# ✅ Celery Workers - Checklist

## 📋 Созданные файлы

### ✅ Основные файлы

- [x] `app/workers/celery_app.py` (~80 строк) - Конфигурация Celery
- [x] `app/workers/__init__.py` (~6 строк) - Экспорты
- [x] `app/workers/README.md` (~300 строк) - Документация

### ✅ Задачи (Tasks)

- [x] `app/workers/tasks/__init__.py` (~3 строки) - Пустой файл
- [x] `app/workers/tasks/parsing.py` (~150 строк) - Парсинг Instagram
- [x] `app/workers/tasks/processing.py` (~250 строк) - AI обработка
- [x] `app/workers/tasks/posting.py` (~40 строк) - Постинг (placeholder)

### ✅ Тестирование

- [x] `scripts/test_celery_worker.py` (~80 строк) - Тестовый скрипт

### ✅ Конфигурация

- [x] `docker-compose.yml` - Обновлен для Celery workers
- [x] `requirements.txt` - Уже содержит Celery

---

## 🔧 Структура Celery Workers

```
app/workers/
├── celery_app.py          # ✅ Конфигурация Celery (80 строк)
│   ├── Celery app initialization
│   ├── 4 очереди (default, parsing, processing, posting)
│   ├── Task routing
│   ├── Retry настройки
│   └── Beat schedule (2 cron задачи)
│
├── __init__.py            # ✅ Экспорты (6 строк)
├── README.md              # ✅ Документация (300+ строк)
│
└── tasks/
    ├── __init__.py        # ✅ Пустой файл (3 строки)
    │
    ├── parsing.py         # ✅ Парсинг Instagram (150 строк)
    │   ├── AsyncTask (базовый класс)
    │   ├── parse_instagram_accounts (все аккаунты)
    │   └── parse_specific_account (один аккаунт)
    │
    ├── processing.py      # ✅ AI обработка (250 строк)
    │   ├── AsyncTask (базовый класс)
    │   ├── process_pending_posts (batch обработка)
    │   └── process_single_post (один пост: AI + images + upload)
    │
    └── posting.py         # ✅ Постинг (40 строк - placeholder)
        └── post_to_instagram (TODO: реализация)
```

---

## 🎯 Функциональность

### ✅ 1. Celery App Configuration (`celery_app.py`)

- [x] Инициализация Celery с broker/backend (Redis)
- [x] 4 очереди: default, parsing, processing, posting
- [x] Task routing по очередям
- [x] Retry настройки (acks_late, reject_on_worker_lost)
- [x] Worker limits (prefetch=1, max_tasks=100)
- [x] Result expiration (1 час)
- [x] Beat schedule:
  - [x] `parse_instagram_accounts` - каждые 6 часов
  - [x] `process_pending_posts` - каждый час

### ✅ 2. Parsing Tasks (`tasks/parsing.py`)

#### ✅ `parse_instagram_accounts`
- [x] Парсит все аккаунты из конфига
- [x] Фильтрует вирусные посты (min_likes, max_age_days)
- [x] Сохраняет в БД со статусом FILTERED
- [x] Триггерит `process_single_post` для каждого нового поста
- [x] Retry: 3 попытки, 5 минут задержка
- [x] Возвращает статистику: fetched, saved, triggered_processing

#### ✅ `parse_specific_account`
- [x] Парсит один конкретный аккаунт
- [x] Сохраняет посты в БД
- [x] Триггерит обработку
- [x] Retry: 2 попытки

### ✅ 3. Processing Tasks (`tasks/processing.py`)

#### ✅ `process_pending_posts`
- [x] Находит все посты со статусом FILTERED
- [x] Обрабатывает по 5 за раз
- [x] Запускает `process_single_post` для каждого с задержкой
- [x] Retry: 2 попытки

#### ✅ `process_single_post`
- [x] **Step 1/3: AI Rewrite**
  - [x] Вызывает AIRewriter
  - [x] Получает title, caption, hashtags, slides
  - [x] Логирует tokens_used и cost_usd
- [x] **Step 2/3: Generate Images**
  - [x] Вызывает CarouselGenerator
  - [x] Генерирует 8 слайдов (1080x1080)
- [x] **Step 3/3: Upload to Yandex.Disk**
  - [x] Вызывает YandexDiskUploader
  - [x] Загружает изображения
  - [x] Получает folder_url
- [x] **Сохранение в БД**
  - [x] Создает ProcessedPost
  - [x] Обновляет статус OriginalPost -> PROCESSED
  - [x] Статус ProcessedPost -> PENDING_APPROVAL
- [x] **Error Handling**
  - [x] Откатывает статус при ошибке
  - [x] Retry: 3 попытки, 10 минут задержка
- [x] TODO: Отправка уведомления в Telegram

### ✅ 4. Posting Tasks (`tasks/posting.py`)

#### ✅ `post_to_instagram`
- [x] Placeholder реализация
- [x] Логирует "not_implemented"
- [x] TODO: Instagram Graph API или instagrapi

### ✅ 5. AsyncTask Base Class

- [x] Обертка для async функций в Celery
- [x] Автоматически запускает `asyncio.run()`
- [x] Используется во всех задачах

---

## 🧪 Тестирование

### ✅ `scripts/test_celery_worker.py`

- [x] Тестирует задачи напрямую (без broker)
- [x] Тест 1: Парсинг конкретного аккаунта
- [x] Тест 2: Обработка первого FILTERED поста
- [x] Инициализация БД
- [x] Логирование результатов

---

## 🚀 Запуск

### ✅ Локально

```bash
# 1. Запустить Redis
docker-compose up redis

# 2. Запустить Worker
celery -A app.workers.celery_app worker --loglevel=info

# 3. Запустить Beat (scheduler)
celery -A app.workers.celery_app beat --loglevel=info

# 4. Тестирование
python scripts/test_celery_worker.py
```

### ✅ Docker Compose

```bash
# Запустить все сервисы
docker-compose up

# Только Celery
docker-compose up celery_worker celery_beat
```

---

## ⚙️ Конфигурация

### ✅ `.env` переменные

```env
# Celery (используются из config.py)
CELERY_BROKER_URL=redis://localhost:6379/0      # Опционально (по умолчанию REDIS_URL)
CELERY_RESULT_BACKEND=redis://localhost:6379/0  # Опционально (по умолчанию REDIS_URL)

# Redis (основной)
REDIS_URL=redis://localhost:6379/0

# Расписание
PARSE_CRON=0 */6 * * *     # Каждые 6 часов
PROCESS_CRON=0 * * * *      # Каждый час
```

### ✅ `app/config.py` - Computed Properties

- [x] `celery_broker` -> возвращает CELERY_BROKER_URL или REDIS_URL
- [x] `celery_backend` -> возвращает CELERY_RESULT_BACKEND или REDIS_URL

---

## 📊 Очереди и Роутинг

| Очередь | Задачи | Routing Key |
|---------|--------|-------------|
| `default` | Общие задачи | `default` |
| `parsing` | `parse_instagram_accounts`, `parse_specific_account` | `parsing` |
| `processing` | `process_pending_posts`, `process_single_post` | `processing` |
| `posting` | `post_to_instagram` | `posting` |

---

## 📅 Beat Schedule (Cron)

| Задача | Расписание | Очередь | Описание |
|--------|-----------|---------|----------|
| `parse_instagram_accounts` | `*/6 * * * *` (каждые 6 часов) | `parsing` | Парсит все аккаунты |
| `process_pending_posts` | `0 * * * *` (каждый час) | `processing` | Обрабатывает FILTERED посты |

---

## 🔄 Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    CELERY BEAT (Scheduler)                   │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │ parse_instagram_     │      │ process_pending_     │    │
│  │ accounts (6h)        │      │ posts (1h)           │    │
│  └──────────┬───────────┘      └──────────┬───────────┘    │
└─────────────┼──────────────────────────────┼────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      PARSING QUEUE                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ parse_instagram_accounts                             │  │
│  │   ├─> Fetch viral posts from Instagram              │  │
│  │   ├─> Filter by likes & age                          │  │
│  │   ├─> Save to DB (status: FILTERED)                  │  │
│  │   └─> Trigger process_single_post for each          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING QUEUE                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ process_single_post                                   │  │
│  │   ├─> Step 1: AI Rewrite (OpenRouter)               │  │
│  │   │    └─> title, caption, hashtags, slides         │  │
│  │   ├─> Step 2: Generate Images (Orshot)              │  │
│  │   │    └─> 8 slides (1080x1080)                     │  │
│  │   ├─> Step 3: Upload to Yandex.Disk                 │  │
│  │   │    └─> folder_url                               │  │
│  │   ├─> Save ProcessedPost to DB                      │  │
│  │   │    └─> status: PENDING_APPROVAL                 │  │
│  │   └─> Update OriginalPost status -> PROCESSED       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
                    (TODO: Telegram notification)
                              │
                              ▼
                    (TODO: Manual approval)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     POSTING QUEUE                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ post_to_instagram (TODO)                             │  │
│  │   ├─> Publish to Instagram                           │  │
│  │   └─> Update status -> POSTED                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Error Handling & Retry

| Задача | Max Retries | Retry Delay | Backoff |
|--------|------------|-------------|---------|
| `parse_instagram_accounts` | 3 | 5 минут | Exponential |
| `parse_specific_account` | 2 | 5 минут | Exponential |
| `process_pending_posts` | 2 | 5 минут | Exponential |
| `process_single_post` | 3 | 10 минут | Exponential |
| `post_to_instagram` | 3 | 5 минут | Exponential |

### ✅ Error Recovery

- [x] При ошибке в `process_single_post` откатывается статус поста
- [x] Задачи используют `task_acks_late=True` (ACK после выполнения)
- [x] `task_reject_on_worker_lost=True` (переотправка при падении worker)
- [x] Логирование всех ошибок через loguru

---

## 📈 Мониторинг

### ✅ Flower (Web UI)

```bash
pip install flower
celery -A app.workers.celery_app flower
# http://localhost:5555
```

### ✅ Celery Inspect

```bash
# Активные задачи
celery -A app.workers.celery_app inspect active

# Очереди
celery -A app.workers.celery_app inspect active_queues

# Статистика
celery -A app.workers.celery_app inspect stats
```

---

## 📝 TODO

- [ ] Реализовать `post_to_instagram` (Instagram Graph API или instagrapi)
- [ ] Добавить отправку уведомлений в Telegram после обработки
- [ ] Добавить систему одобрения постов через Telegram
- [ ] Добавить мониторинг через Flower
- [ ] Добавить метрики (Prometheus)
- [ ] Добавить алерты (Sentry)
- [ ] Добавить rate limiting для API вызовов
- [ ] Добавить приоритеты для задач
- [ ] Добавить dead letter queue для failed tasks

---

## ✅ Итоговая статистика

### Созданные файлы: 8

1. `app/workers/celery_app.py` - 80 строк
2. `app/workers/__init__.py` - 6 строк
3. `app/workers/README.md` - 300+ строк
4. `app/workers/tasks/__init__.py` - 3 строки
5. `app/workers/tasks/parsing.py` - 150 строк
6. `app/workers/tasks/processing.py` - 250 строк
7. `app/workers/tasks/posting.py` - 40 строк
8. `scripts/test_celery_worker.py` - 80 строк

### Обновленные файлы: 1

1. `docker-compose.yml` - Исправлены пути для Celery workers

### Общий объем кода: ~900 строк

---

## 🎉 Готово к использованию!

Все Celery workers созданы и готовы к запуску. Следуй инструкциям в README для тестирования.
