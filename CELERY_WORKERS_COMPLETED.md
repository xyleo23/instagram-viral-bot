# ✅ Celery Workers - COMPLETED

## 🎉 Все файлы успешно созданы!

---

## 📦 Созданные файлы (8 файлов)

### 1. Конфигурация Celery

#### ✅ `app/workers/celery_app.py` (80 строк)

**Содержимое:**
- Инициализация Celery приложения
- Конфигурация broker/backend (Redis)
- 4 очереди: `default`, `parsing`, `processing`, `posting`
- Task routing по очередям
- Retry настройки
- Worker limits
- Beat schedule (2 cron задачи)

**Ключевые настройки:**
```python
celery_app = Celery(
    "instagram_viral_bot",
    broker=config.celery_broker,
    backend=config.celery_backend,
    include=[
        "app.workers.tasks.parsing",
        "app.workers.tasks.processing",
        "app.workers.tasks.posting"
    ]
)
```

**Beat Schedule:**
- `parse_instagram_accounts` - каждые 6 часов
- `process_pending_posts` - каждый час

---

### 2. Задачи парсинга

#### ✅ `app/workers/tasks/parsing.py` (150 строк)

**Задачи:**

1. **`parse_instagram_accounts`**
   - Парсит все аккаунты из конфига
   - Фильтрует вирусные посты (min_likes, max_age_days)
   - Сохраняет в БД со статусом `FILTERED`
   - Триггерит `process_single_post` для каждого поста
   - Retry: 3 попытки, 5 минут задержка

2. **`parse_specific_account`**
   - Парсит один конкретный аккаунт
   - Сохраняет посты в БД
   - Триггерит обработку
   - Retry: 2 попытки

**Возвращаемые данные:**
```python
{
    "status": "success",
    "fetched": 15,
    "saved": 8,
    "triggered_processing": 8
}
```

---

### 3. Задачи обработки

#### ✅ `app/workers/tasks/processing.py` (250 строк)

**Задачи:**

1. **`process_pending_posts`**
   - Находит все посты со статусом `FILTERED`
   - Обрабатывает по 5 за раз
   - Запускает `process_single_post` для каждого
   - Retry: 2 попытки

2. **`process_single_post`** (главная задача)
   - **Step 1/3: AI Rewrite**
     - Вызывает `AIRewriter`
     - Получает title, caption, hashtags, slides
     - Логирует tokens_used и cost_usd
   
   - **Step 2/3: Generate Images**
     - Вызывает `CarouselGenerator`
     - Генерирует 8 слайдов (1080x1080)
   
   - **Step 3/3: Upload to Yandex.Disk**
     - Вызывает `YandexDiskUploader`
     - Загружает изображения
     - Получает folder_url
   
   - **Сохранение в БД**
     - Создает `ProcessedPost`
     - Обновляет статус `OriginalPost` -> `PROCESSED`
     - Статус `ProcessedPost` -> `PENDING_APPROVAL`
   
   - **Error Handling**
     - Откатывает статус при ошибке
     - Retry: 3 попытки, 10 минут задержка

**Возвращаемые данные:**
```python
{
    "status": "success",
    "post_id": 1,
    "processed_post_id": 1,
    "cost_usd": 0.0234,
    "yandex_url": "https://disk.yandex.ru/..."
}
```

---

### 4. Задачи постинга

#### ✅ `app/workers/tasks/posting.py` (40 строк - placeholder)

**Задачи:**

1. **`post_to_instagram`** (TODO)
   - Placeholder реализация
   - Логирует "not_implemented"
   - TODO: Instagram Graph API или instagrapi

---

### 5. Инициализация

#### ✅ `app/workers/__init__.py` (6 строк)

```python
from app.workers.celery_app import celery_app
from app.workers.tasks import parsing, processing, posting

__all__ = ["celery_app", "parsing", "processing", "posting"]
```

#### ✅ `app/workers/tasks/__init__.py` (3 строки)

Пустой файл для импорта задач.

---

### 6. Тестирование

#### ✅ `scripts/test_celery_worker.py` (80 строк)

**Функциональность:**
- Тестирует задачи напрямую (без broker)
- Тест 1: Парсинг конкретного аккаунта
- Тест 2: Обработка первого `FILTERED` поста
- Инициализация БД
- Логирование результатов

**Запуск:**
```bash
python scripts/test_celery_worker.py
```

---

### 7. Документация

#### ✅ `app/workers/README.md` (300+ строк)

**Содержимое:**
- Структура проекта
- Инструкции по запуску
- Описание очередей
- Расписание задач
- Workflow диаграммы
- Retry стратегия
- Мониторинг (Flower)
- Production настройки (Supervisor, Systemd)
- Troubleshooting

#### ✅ `CELERY_WORKERS_CHECKLIST.md` (400+ строк)

**Содержимое:**
- Полный чеклист созданных файлов
- Детальное описание каждой задачи
- Workflow диаграммы
- Error handling
- Мониторинг
- TODO список

#### ✅ `QUICK_START_CELERY.md` (200+ строк)

**Содержимое:**
- Быстрый старт (3 способа запуска)
- Проверка работы
- Тестирование
- Мониторинг
- Управление задачами
- Troubleshooting
- Примеры использования

---

## 🔧 Обновленные файлы (1 файл)

### ✅ `docker-compose.yml`

**Изменения:**
- Исправлены пути для Celery workers (`src` -> `app`)
- Команды обновлены: `celery -A app.workers.celery_app`

```yaml
celery_worker:
  command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=2

celery_beat:
  command: celery -A app.workers.celery_app beat --loglevel=info
```

---

## 📊 Статистика

| Метрика | Значение |
|---------|----------|
| Всего файлов создано | 8 |
| Всего файлов обновлено | 1 |
| Общий объем кода | ~900 строк |
| Документация | ~900 строк |
| **ИТОГО** | **~1800 строк** |

---

## 🏗️ Архитектура

```
app/workers/
├── celery_app.py          # 80 строк - Конфигурация Celery
├── __init__.py            # 6 строк - Экспорты
├── README.md              # 300+ строк - Документация
└── tasks/
    ├── __init__.py        # 3 строки - Пустой файл
    ├── parsing.py         # 150 строк - Парсинг Instagram
    ├── processing.py      # 250 строк - AI обработка
    └── posting.py         # 40 строк - Постинг (placeholder)

scripts/
└── test_celery_worker.py  # 80 строк - Тестирование

docs/
├── CELERY_WORKERS_CHECKLIST.md  # 400+ строк
├── QUICK_START_CELERY.md        # 200+ строк
└── CELERY_WORKERS_COMPLETED.md  # Этот файл
```

---

## 🔄 Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    CELERY BEAT (Scheduler)                   │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │ Every 6 hours        │      │ Every hour           │    │
│  └──────────┬───────────┘      └──────────┬───────────┘    │
└─────────────┼──────────────────────────────┼────────────────┘
              │                              │
              ▼                              ▼
      parse_instagram_accounts    process_pending_posts
              │                              │
              ▼                              ▼
    ┌─────────────────┐          ┌─────────────────┐
    │ Fetch viral     │          │ Find FILTERED   │
    │ posts           │          │ posts           │
    └────────┬────────┘          └────────┬────────┘
             │                            │
             ▼                            ▼
    ┌─────────────────┐          ┌─────────────────┐
    │ Save to DB      │          │ Queue           │
    │ (FILTERED)      │          │ processing      │
    └────────┬────────┘          └────────┬────────┘
             │                            │
             └────────────┬───────────────┘
                          │
                          ▼
                 process_single_post
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   AI Rewrite      Generate Images   Upload to Yandex
   (OpenRouter)    (Orshot)           (Yandex.Disk)
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          ▼
                 Save ProcessedPost
                 (PENDING_APPROVAL)
                          │
                          ▼
            TODO: Telegram notification
                          │
                          ▼
            TODO: Manual approval
                          │
                          ▼
                 post_to_instagram
                 (TODO: Instagram API)
```

---

## 🚀 Запуск

### Способ 1: Локально

```bash
# Терминал 1: Redis
docker-compose up redis

# Терминал 2: Worker
celery -A app.workers.celery_app worker --loglevel=info

# Терминал 3: Beat
celery -A app.workers.celery_app beat --loglevel=info
```

### Способ 2: Docker Compose (рекомендуется)

```bash
docker-compose up celery_worker celery_beat
```

### Способ 3: Тестирование

```bash
python scripts/test_celery_worker.py
```

---

## ✅ Проверка

### 1. Проверить Redis

```bash
redis-cli ping
# Ожидаемый ответ: PONG
```

### 2. Проверить Celery Worker

```bash
celery -A app.workers.celery_app inspect active
```

### 3. Проверить очереди

```bash
celery -A app.workers.celery_app inspect active_queues
# Ожидаемый вывод: default, parsing, processing, posting
```

---

## 📋 Очереди

| Очередь | Задачи | Routing Key |
|---------|--------|-------------|
| `default` | Общие задачи | `default` |
| `parsing` | `parse_instagram_accounts`, `parse_specific_account` | `parsing` |
| `processing` | `process_pending_posts`, `process_single_post` | `processing` |
| `posting` | `post_to_instagram` | `posting` |

---

## 📅 Beat Schedule

| Задача | Расписание | Очередь | Описание |
|--------|-----------|---------|----------|
| `parse_instagram_accounts` | `*/6 * * * *` | `parsing` | Парсит все аккаунты из конфига |
| `process_pending_posts` | `0 * * * *` | `processing` | Обрабатывает FILTERED посты |

---

## 🛡️ Error Handling

| Задача | Max Retries | Retry Delay |
|--------|------------|-------------|
| `parse_instagram_accounts` | 3 | 5 минут |
| `parse_specific_account` | 2 | 5 минут |
| `process_pending_posts` | 2 | 5 минут |
| `process_single_post` | 3 | 10 минут |
| `post_to_instagram` | 3 | 5 минут |

---

## 📈 Мониторинг

### Flower (Web UI)

```bash
pip install flower
celery -A app.workers.celery_app flower
# http://localhost:5555
```

### Celery Inspect

```bash
# Активные задачи
celery -A app.workers.celery_app inspect active

# Статистика
celery -A app.workers.celery_app inspect stats
```

---

## 📝 TODO

- [ ] Реализовать `post_to_instagram` (Instagram Graph API)
- [ ] Добавить Telegram уведомления после обработки
- [ ] Добавить систему одобрения через Telegram
- [ ] Добавить мониторинг через Flower
- [ ] Добавить метрики (Prometheus)
- [ ] Добавить алерты (Sentry)

---

## 🎯 Следующие шаги

1. ✅ **Запустить Redis**
   ```bash
   docker-compose up redis -d
   ```

2. ✅ **Запустить Celery Worker**
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```

3. ✅ **Запустить Celery Beat**
   ```bash
   celery -A app.workers.celery_app beat --loglevel=info
   ```

4. ✅ **Протестировать**
   ```bash
   python scripts/test_celery_worker.py
   ```

5. ⏳ **Дождаться автоматического парсинга** (через 6 часов)

6. ⏳ **Проверить обработанные посты в БД**

---

## 📚 Документация

- [app/workers/README.md](app/workers/README.md) - Подробная документация
- [CELERY_WORKERS_CHECKLIST.md](CELERY_WORKERS_CHECKLIST.md) - Полный чеклист
- [QUICK_START_CELERY.md](QUICK_START_CELERY.md) - Быстрый старт

---

## 🎉 Готово!

Все Celery workers успешно созданы и готовы к использованию!

### Что было создано:

✅ Конфигурация Celery с 4 очередями  
✅ Задачи парсинга Instagram  
✅ Задачи AI обработки (AI + Images + Upload)  
✅ Задачи постинга (placeholder)  
✅ Автоматическое расписание (Beat)  
✅ Error handling & retry  
✅ Тестовый скрипт  
✅ Полная документация  

### Общий объем: ~1800 строк кода и документации

---

**Дата создания:** 30 января 2026  
**Статус:** ✅ COMPLETED
