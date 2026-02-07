# 🚀 Быстрый старт: Система одобрения постов

## Что обновлено

✅ `app/bot/handlers/approval.py` - полная реализация (~350 строк)
- Функция `send_post_for_approval()` - отправка превью с изображениями
- Подготовка медиа-группы из base64/URL
- Красивое форматирование текста
- FSM для редактирования caption/hashtags
- Callback handlers для всех действий

✅ `app/workers/tasks/processing.py` - интеграция уведомлений
- Автоматическая отправка после обработки поста
- Отправка уведомления админу в Telegram

✅ `scripts/test_approval_notification.py` - тестовый скрипт
- Создание тестового ProcessedPost
- Отправка уведомления для проверки

✅ `docs/APPROVAL_SYSTEM.md` - полная документация
- Архитектура системы
- Описание всех компонентов
- Troubleshooting

## Предварительные требования

1. **Redis** должен быть запущен (для FSM storage):
```bash
# Windows (если установлен)
redis-server

# Или через Docker
docker run -d -p 6379:6379 redis:alpine
```

2. **Переменные окружения** в `.env`:
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_CHAT_ID=your_telegram_user_id
REDIS_URL=redis://localhost:6379/0
```

3. **База данных** инициализирована:
```bash
alembic upgrade head
```

## 🎯 Пошаговый запуск

### Шаг 1: Запустите Redis

```bash
# Проверьте, что Redis запущен
redis-cli ping
# Должно вернуть: PONG
```

### Шаг 2: Запустите Telegram бота

```bash
python -m app.bot.main
```

**Ожидаемый вывод:**
```
2025-01-30 12:00:00 | INFO | Starting Instagram Viral Bot...
2025-01-30 12:00:00 | INFO | Database initialized
2025-01-30 12:00:00 | INFO | All handlers registered
2025-01-30 12:00:00 | INFO | Bot started. Polling...
```

В Telegram вы получите сообщение:
```
🤖 Instagram Viral Bot запущен!

Используйте /start для начала работы.
```

### Шаг 3: Запустите Celery worker (в новом терминале)

```bash
celery -A app.workers.celery_app worker -l INFO
```

**Ожидаемый вывод:**
```
[tasks]
  . app.workers.tasks.processing.process_pending_posts
  . app.workers.tasks.processing.process_single_post

[2025-01-30 12:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/1
[2025-01-30 12:00:00,000: INFO/MainProcess] Ready to receive tasks
```

### Шаг 4: Тестирование системы

#### Вариант А: Тест уведомления (быстрый)

```bash
python scripts/test_approval_notification.py
```

**Что произойдет:**
1. Создается тестовый `ProcessedPost` (если нет существующего)
2. Отправляется уведомление админу в Telegram
3. Вы получите:
   - Медиа-группу с изображениями (2 тестовых слайда)
   - Текст с информацией о посте
   - Интерактивные кнопки

#### Вариант Б: Полный тест обработки (полный цикл)

```bash
# В третьем терминале
python scripts/test_celery_worker.py
```

**Что произойдет:**
1. Worker обработает пост через AI
2. Сгенерирует карусель
3. Загрузит на Яндекс.Диск
4. Автоматически отправит уведомление админу

## 📱 Проверка в Telegram

### 1. Вы должны получить:

**Сообщение 1: Медиа-группа**
- Карусель изображений (до 10 слайдов)
- Красивые слайды с текстом

**Сообщение 2: Текст с кнопками**
```
📊 НОВЫЙ ПОСТ НА ПРОВЕРКУ

Источник:
👤 Author: @testuser
❤️ Likes: 5,000
💬 Comments: 120
🔗 Оригинал

━━━━━━━━━━━━━━━━━━━━

📝 Новый контент:

🚀 Тестовый заголовок: Как достичь успеха

Это тестовый пост...

#тест #проверка #бот #успех

━━━━━━━━━━━━━━━━━━━━

📊 Метрики:
🤖 AI Model: openrouter/anthropic/claude-3.5-sonnet
🔢 Tokens: 1,500
💰 Cost: $0.0075
🖼 Slides: 3

Выберите действие:
```

**Кнопки:**
- ✅ Одобрить
- ❌ Отклонить
- ✏️ Редактировать текст
- 🏷 Изменить хештеги
- 🔗 Открыть на Яндекс.Диске

### 2. Тестирование кнопок

#### ✅ Одобрить
1. Нажмите "✅ Одобрить"
2. Сообщение обновится:
```
✅ Пост одобрен!

ID: 1
Статус: APPROVED
Одобрил: @yourusername

Пост готов к публикации.
```

#### ❌ Отклонить
1. Нажмите "❌ Отклонить"
2. Сообщение обновится:
```
❌ Пост отклонен

ID: 1
Статус: REJECTED
Отклонил: @yourusername
```

#### ✏️ Редактировать текст
1. Нажмите "✏️ Редактировать текст"
2. Получите запрос:
```
✏️ Редактирование текста

Отправьте новый текст для поста.
Для отмены отправьте /cancel
```
3. Отправьте новый текст
4. Получите подтверждение:
```
✅ Текст обновлен!

Новый текст:
Ваш новый текст...
```

#### 🏷 Изменить хештеги
1. Нажмите "🏷 Изменить хештеги"
2. Получите запрос:
```
🏷 Редактирование хештегов

Отправьте новые хештеги (через пробел).
Пример: #бизнес #мотивация #успех

Для отмены отправьте /cancel
```
3. Отправьте новые хештеги
4. Получите подтверждение:
```
✅ Хештеги обновлены!

Новые хештеги:
#новые #хештеги
```

## 🐛 Troubleshooting

### Бот не запускается

**Проблема:** `aiogram.exceptions.TelegramUnauthorizedError`
**Решение:** Проверьте `BOT_TOKEN` в `.env`

**Проблема:** `ConnectionRefusedError: [Errno 111] Connection refused` (Redis)
**Решение:** Запустите Redis:
```bash
docker run -d -p 6379:6379 redis:alpine
```

### Уведомления не приходят

**Проблема:** Бот отправляет сообщения не туда
**Решение:** 
1. Узнайте свой Telegram ID:
   - Отправьте `/start` боту @userinfobot
   - Скопируйте ID
   - Обновите `ADMIN_CHAT_ID` в `.env`

**Проблема:** `ProcessedPost not found`
**Решение:** Запустите тестовый скрипт:
```bash
python scripts/test_approval_notification.py
```

### Изображения не отображаются

**Проблема:** Вместо изображений только текст
**Решение:**
1. Проверьте `image_urls` в `ProcessedPost`:
```python
# Должны быть base64 или URL:
["data:image/png;base64,...", "https://..."]
```
2. Проверьте логи на ошибки при подготовке медиа-группы

**Проблема:** `Bad Request: wrong file identifier/HTTP URL specified`
**Решение:** URL изображений должны быть публичными и доступными

### FSM не работает

**Проблема:** После нажатия "Редактировать" ничего не происходит
**Решение:**
1. Убедитесь, что Redis запущен
2. Проверьте `REDIS_URL` в `.env`
3. Перезапустите бота

**Проблема:** Бот не реагирует на отправленный текст
**Решение:**
1. Проверьте, что `FSMContext` передается в handlers:
```python
async def callback_edit_caption(callback: CallbackQuery, state: FSMContext):
```
2. Проверьте, что роутер зарегистрирован в `main.py`

## 📊 Проверка в БД

### ApprovalHistory
```sql
SELECT * FROM approval_history ORDER BY timestamp DESC LIMIT 5;
```

**Ожидаемые записи:**
- `user_id` - ваш Telegram ID
- `decision` - `APPROVED` или `REJECTED`
- `timestamp` - время действия

### ProcessedPost статусы
```sql
SELECT id, title, status, created_at 
FROM processed_posts 
ORDER BY created_at DESC 
LIMIT 5;
```

**Статусы:**
- `pending_approval` - ожидает одобрения
- `approved` - одобрен
- `rejected` - отклонен

## ✅ Checklist

- [ ] Redis запущен (`redis-cli ping` возвращает `PONG`)
- [ ] Telegram бот запущен (`python -m app.bot.main`)
- [ ] Celery worker запущен (`celery -A app.workers.celery_app worker -l INFO`)
- [ ] Тестовое уведомление отправлено (`python scripts/test_approval_notification.py`)
- [ ] Получено сообщение в Telegram с изображениями
- [ ] Кнопка "✅ Одобрить" работает (статус меняется на `APPROVED`)
- [ ] Кнопка "❌ Отклонить" работает (статус меняется на `REJECTED`)
- [ ] Кнопка "✏️ Редактировать текст" работает (FSM запускается)
- [ ] Кнопка "🏷 Изменить хештеги" работает (FSM запускается)
- [ ] Записи создаются в `approval_history`

## 📚 Дополнительные ресурсы

- **Полная документация:** `docs/APPROVAL_SYSTEM.md`
- **Архитектура проекта:** `PROJECT_STRUCTURE.md`
- **Конфигурация:** `.env.example`

## 🎉 Готово!

Если все чеклисты пройдены ✅, система одобрения постов полностью работает!

**Следующие шаги:**
1. Интеграция с реальным парсером Instagram
2. Планировщик публикаций
3. Публикация в Instagram через API
4. Аналитика и отчеты

---

**Вопросы?** Проверьте логи:
- Бот: `logs/bot.log`
- Worker: `logs/worker.log`
- Celery: консоль worker
