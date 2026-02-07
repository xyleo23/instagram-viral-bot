# 🔧 Celery Workers для Instagram Viral Bot

Автоматизация парсинга, обработки и постинга через Celery.

## 📁 Структура

```
app/workers/
├── celery_app.py          # Конфигурация Celery
├── __init__.py            # Экспорты
└── tasks/
    ├── __init__.py
    ├── parsing.py         # Задачи парсинга Instagram
    ├── processing.py      # Задачи AI обработки
    └── posting.py         # Задачи постинга (placeholder)
```

## 🚀 Запуск

### 1. Запуск Redis (broker)

```bash
# Docker
docker-compose up redis

# Или локально
redis-server
```

### 2. Запуск Celery Worker

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

### 3. Запуск Celery Beat (scheduler)

```bash
celery -A app.workers.celery_app beat --loglevel=info
```

### 4. Запуск через Docker Compose

```bash
docker-compose up celery_worker celery_beat
```

## 📋 Очереди

| Очередь | Назначение | Задачи |
|---------|-----------|--------|
| `default` | Общие задачи | - |
| `parsing` | Парсинг Instagram | `parse_instagram_accounts`, `parse_specific_account` |
| `processing` | AI обработка | `process_pending_posts`, `process_single_post` |
| `posting` | Постинг в Instagram | `post_to_instagram` |

## 📅 Расписание (Celery Beat)

| Задача | Расписание | Описание |
|--------|-----------|----------|
| `parse_instagram_accounts` | Каждые 6 часов | Парсит все аккаунты из конфига |
| `process_pending_posts` | Каждый час | Обрабатывает посты со статусом FILTERED |

## 🔄 Workflow

### 1. Парсинг Instagram

```
parse_instagram_accounts
  ↓
Fetches viral posts from Instagram
  ↓
Saves to DB with status FILTERED
  ↓
Triggers process_single_post for each
```

### 2. AI Обработка

```
process_single_post
  ↓
AI Rewrite (OpenRouter)
  ↓
Generate carousel images (Orshot)
  ↓
Upload to Yandex.Disk
  ↓
Save ProcessedPost to DB
  ↓
Send Telegram notification (TODO)
```

### 3. Постинг (TODO)

```
post_to_instagram
  ↓
Publish to Instagram
  ↓
Update status to POSTED
```

## 🧪 Тестирование

### Прямое тестирование (без broker)

```bash
python scripts/test_celery_worker.py
```

### Ручной запуск задачи

```python
from app.workers.tasks.parsing import parse_specific_account

# Через Celery (async)
result = parse_specific_account.apply_async(args=["username"])
print(result.get())

# Напрямую (sync)
result = parse_specific_account.run_async(
    parse_specific_account,
    username="username"
)
```

## ⚙️ Конфигурация

Настройки в `.env`:

```env
# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Расписание
PARSE_CRON=0 */6 * * *     # Каждые 6 часов
PROCESS_CRON=0 * * * *      # Каждый час
```

## 🛠️ Retry стратегия

| Задача | Max Retries | Retry Delay |
|--------|------------|-------------|
| `parse_instagram_accounts` | 3 | 5 минут |
| `parse_specific_account` | 2 | 5 минут |
| `process_pending_posts` | 2 | 5 минут |
| `process_single_post` | 3 | 10 минут |
| `post_to_instagram` | 3 | 5 минут |

## 📊 Мониторинг

### Flower (Web UI для Celery)

```bash
pip install flower
celery -A app.workers.celery_app flower
```

Откройте: http://localhost:5555

### Логи

```bash
# Worker logs
tail -f logs/bot.log

# Celery logs
celery -A app.workers.celery_app worker --loglevel=debug
```

## 🔥 Production настройки

### Supervisor (Linux)

```ini
[program:celery_worker]
command=celery -A app.workers.celery_app worker --loglevel=info
directory=/path/to/instagram_bot
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery_worker.log

[program:celery_beat]
command=celery -A app.workers.celery_app beat --loglevel=info
directory=/path/to/instagram_bot
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery_beat.log
```

### Systemd (Linux)

```ini
# /etc/systemd/system/celery_worker.service
[Unit]
Description=Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/instagram_bot
ExecStart=/usr/local/bin/celery -A app.workers.celery_app worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🐛 Troubleshooting

### Worker не запускается

```bash
# Проверьте Redis
redis-cli ping

# Проверьте конфигурацию
python -c "from app.config import get_config; print(get_config().celery_broker)"

# Проверьте импорты
python -c "from app.workers.celery_app import celery_app; print(celery_app)"
```

### Задачи не выполняются

```bash
# Проверьте очереди
celery -A app.workers.celery_app inspect active_queues

# Проверьте активные задачи
celery -A app.workers.celery_app inspect active

# Очистите очереди
celery -A app.workers.celery_app purge
```

### Задачи зависают

```bash
# Отмените все задачи
celery -A app.workers.celery_app control revoke <task_id>

# Перезапустите worker
celery -A app.workers.celery_app control shutdown
celery -A app.workers.celery_app worker --loglevel=info
```

## 📚 Дополнительно

- [Celery Documentation](https://docs.celeryproject.org/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html#best-practices)
- [Flower Documentation](https://flower.readthedocs.io/)
