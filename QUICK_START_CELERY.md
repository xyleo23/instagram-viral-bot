# 🚀 Quick Start - Celery Workers

Быстрый запуск Celery workers для автоматизации Instagram Viral Bot.

---

## 📋 Предварительные требования

### 1. Установлены зависимости

```bash
pip install -r requirements.txt
```

### 2. Настроен `.env` файл

```env
# Database
DATABASE_URL=postgresql+asyncpg://instagram_bot:password@localhost:5432/instagram_viral

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
APIFY_API_KEY=your_apify_key
OPENROUTER_API_KEY=your_openrouter_key
ORSHOT_API_KEY=your_orshot_key
YANDEX_DISK_TOKEN=your_yandex_token

# Instagram
INSTAGRAM_AUTHORS=sanyaagainst,theivansergeev,ivan.loginov_ai
MIN_LIKES=5000
MAX_POST_AGE_DAYS=3
```

### 3. Запущены сервисы

```bash
# PostgreSQL и Redis
docker-compose up postgres redis -d
```

---

## 🏃 Запуск (3 способа)

### Способ 1: Локально (для разработки)

#### Терминал 1: Redis

```bash
docker-compose up redis
```

#### Терминал 2: Celery Worker

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

#### Терминал 3: Celery Beat (опционально)

```bash
celery -A app.workers.celery_app beat --loglevel=info
```

---

### Способ 2: Docker Compose (рекомендуется)

```bash
# Запустить все сервисы
docker-compose up

# Или только Celery workers
docker-compose up celery_worker celery_beat
```

---

### Способ 3: Тестирование без broker

```bash
# Прямой запуск задач (без Redis)
python scripts/test_celery_worker.py
```

---

## ✅ Проверка работы

### 1. Проверить Redis

```bash
redis-cli ping
# Ожидаемый ответ: PONG
```

### 2. Проверить Celery Worker

```bash
celery -A app.workers.celery_app inspect active
# Должен показать активные задачи
```

### 3. Проверить очереди

```bash
celery -A app.workers.celery_app inspect active_queues
# Должен показать: default, parsing, processing, posting
```

---

## 🧪 Тестирование

### Тест 1: Парсинг одного аккаунта

```python
from app.workers.tasks.parsing import parse_specific_account

# Запустить задачу
result = parse_specific_account.apply_async(args=["sanyaagainst"])

# Получить результат
print(result.get(timeout=60))
# Ожидаемый вывод: {"username": "sanyaagainst", "fetched": 5, "saved": 2}
```

### Тест 2: Обработка поста

```python
from app.workers.tasks.processing import process_single_post

# Запустить обработку поста с ID=1
result = process_single_post.apply_async(args=[1])

# Получить результат
print(result.get(timeout=300))  # 5 минут таймаут
# Ожидаемый вывод: {"status": "success", "post_id": 1, "processed_post_id": 1, ...}
```

### Тест 3: Полный workflow

```bash
python scripts/test_celery_worker.py
```

Ожидаемый вывод:

```
🔧 Testing Celery Tasks

1. Testing parsing task...
   ✅ Parsed: {'username': 'sanyaagainst', 'fetched': 5, 'saved': 2}

2. Testing processing task...
   ✅ Processed: {'status': 'success', 'post_id': 1, 'processed_post_id': 1, 'cost_usd': 0.0234, 'yandex_url': 'https://...'}

✅ All tests completed!
```

---

## 📊 Мониторинг

### Flower (Web UI)

```bash
# Установить Flower
pip install flower

# Запустить
celery -A app.workers.celery_app flower

# Открыть в браузере
# http://localhost:5555
```

### Логи

```bash
# Worker logs
tail -f logs/bot.log

# Celery logs (подробные)
celery -A app.workers.celery_app worker --loglevel=debug
```

---

## 🔄 Автоматическое расписание

После запуска Celery Beat, задачи будут выполняться автоматически:

| Задача | Расписание | Описание |
|--------|-----------|----------|
| `parse_instagram_accounts` | Каждые 6 часов | Парсит все аккаунты из конфига |
| `process_pending_posts` | Каждый час | Обрабатывает посты со статусом FILTERED |

### Проверить расписание

```bash
celery -A app.workers.celery_app inspect scheduled
```

---

## 🛠️ Управление задачами

### Отменить задачу

```bash
celery -A app.workers.celery_app control revoke <task_id>
```

### Очистить очередь

```bash
celery -A app.workers.celery_app purge
```

### Перезапустить worker

```bash
celery -A app.workers.celery_app control shutdown
celery -A app.workers.celery_app worker --loglevel=info
```

---

## 🐛 Troubleshooting

### Проблема: Worker не запускается

**Решение:**

```bash
# 1. Проверить Redis
redis-cli ping

# 2. Проверить конфигурацию
python -c "from app.config import get_config; print(get_config().celery_broker)"

# 3. Проверить импорты
python -c "from app.workers.celery_app import celery_app; print(celery_app)"
```

### Проблема: Задачи не выполняются

**Решение:**

```bash
# 1. Проверить активные задачи
celery -A app.workers.celery_app inspect active

# 2. Проверить очереди
celery -A app.workers.celery_app inspect active_queues

# 3. Очистить зависшие задачи
celery -A app.workers.celery_app purge
```

### Проблема: Ошибка импорта модулей

**Решение:**

```bash
# Убедитесь, что вы в корневой директории проекта
cd c:\Users\Admin\.cursor\instagram_bot

# Проверьте PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%cd%          # Windows
```

### Проблема: База данных не инициализирована

**Решение:**

```bash
# Инициализировать БД
python scripts/init_db.py
```

---

## 📈 Примеры использования

### Пример 1: Ручной запуск парсинга

```python
from app.workers.tasks.parsing import parse_instagram_accounts

# Запустить парсинг всех аккаунтов
result = parse_instagram_accounts.apply_async()

# Получить результат
print(result.get(timeout=120))
# {"status": "success", "fetched": 15, "saved": 8, "triggered_processing": 8}
```

### Пример 2: Обработка конкретного поста

```python
from app.workers.tasks.processing import process_single_post

# Обработать пост с ID=5
result = process_single_post.apply_async(args=[5])

# Ждать результата
result_data = result.get(timeout=300)
print(f"Processed post: {result_data['processed_post_id']}")
print(f"Cost: ${result_data['cost_usd']:.4f}")
print(f"Yandex URL: {result_data['yandex_url']}")
```

### Пример 3: Batch обработка

```python
from app.workers.tasks.processing import process_pending_posts

# Обработать все FILTERED посты
result = process_pending_posts.apply_async()

# Получить статистику
stats = result.get(timeout=60)
print(f"Found: {stats['found']}, Queued: {stats['queued']}")
```

---

## 🎯 Следующие шаги

1. ✅ Запустить Celery Worker и Beat
2. ✅ Протестировать парсинг: `python scripts/test_celery_worker.py`
3. ✅ Проверить логи: `tail -f logs/bot.log`
4. ✅ Открыть Flower: `http://localhost:5555`
5. ⏳ Дождаться автоматического парсинга (через 6 часов)
6. ⏳ Проверить обработанные посты в БД

---

## 📚 Дополнительная информация

- [Celery Documentation](https://docs.celeryproject.org/)
- [app/workers/README.md](app/workers/README.md) - Подробная документация
- [CELERY_WORKERS_CHECKLIST.md](CELERY_WORKERS_CHECKLIST.md) - Полный чеклист

---

## 🎉 Готово!

Celery workers настроены и готовы к работе. Следуй инструкциям выше для запуска и тестирования.
