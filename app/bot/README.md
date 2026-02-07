# 🤖 Telegram Bot Handlers

Базовые обработчики для Instagram Viral Bot на aiogram 3.10.

## 📁 Структура

```
app/bot/
├── main.py                      # Точка входа бота
├── states.py                    # FSM состояния
├── handlers/
│   ├── __init__.py
│   ├── start.py                 # /start, /help, /status
│   ├── queue.py                 # /queue - просмотр очереди
│   ├── approval.py              # Одобрение/отклонение постов
│   └── history.py               # /history - история постов
├── keyboards/
│   ├── __init__.py
│   └── inline.py                # Inline клавиатуры
└── middlewares/
    ├── __init__.py
    └── logging_middleware.py    # Логирование событий
```

## ✅ Реализованные функции

### 1. Базовые команды (`start.py`)

- **`/start`** - Приветствие и главное меню
- **`/help`** - Справка по командам
- **`/status`** - Статус системы и статистика
  - Посты на одобрении
  - Распарсено сегодня
  - Всего постов
  - Одобрено постов
  - Настройки системы

### 2. Очередь постов (`queue.py`)

- **`/queue`** - Просмотр очереди на одобрение
- Пагинация (5 постов на страницу)
- Навигация: ⬅️ Назад / ➡️ Вперед
- Кнопка 🔄 Обновить

### 3. Одобрение постов (`approval.py`)

- **✅ Одобрить** - Одобрить пост
- **❌ Отклонить** - Отклонить пост
- **✏️ Редактировать текст** - Изменить caption (TODO)
- **🏷 Изменить хештеги** - Изменить hashtags (TODO)
- Сохранение истории решений в БД

### 4. История (`history.py`)

- **`/history`** - Последние 10 обработанных постов
- Показывает одобренные/отклоненные/опубликованные
- Сортировка по дате обновления

### 5. Клавиатуры (`keyboards/inline.py`)

- `get_approval_keyboard()` - Кнопки одобрения
- `get_queue_navigation_keyboard()` - Навигация по очереди
- `get_main_menu_keyboard()` - Главное меню

### 6. Middleware (`middlewares/logging_middleware.py`)

- Логирование всех сообщений
- Логирование всех callback queries
- Обработка ошибок с уведомлением пользователя

### 7. FSM States (`states.py`)

- `ApprovalStates` - Состояния одобрения
  - `waiting_approval`
  - `editing_caption`
  - `editing_hashtags`
- `ManualParsingStates` - Ручной парсинг
  - `waiting_username`

## 🚀 Запуск

### 1. Настройка `.env`

```bash
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_CHAT_ID=123456789

# Redis (для FSM)
REDIS_URL=redis://localhost:6379/0

# Database
DATABASE_URL=sqlite+aiosqlite:///./instagram_bot.db
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Запуск Redis

```bash
# Docker
docker run -d -p 6379:6379 redis:alpine

# Или локально
redis-server
```

### 4. Инициализация БД

```bash
python scripts/init_db.py
```

### 5. Запуск бота

```bash
python -m app.bot.main
```

## 📊 Проверка работы

### 1. Отправьте `/start` боту

Должно появиться:

```
🎉 Добро пожаловать в Instagram Viral Bot!

Я автоматизирую создание вирусного контента для Instagram:

Как работает:
1️⃣ Каждые 6 часов парсю топовых авторов
2️⃣ Фильтрую вирусные посты (5000+ лайков)
...
```

### 2. Отправьте `/status`

Должна показаться статистика:

```
📊 Статус системы

Очередь:
⏳ На одобрении: 0 постов

Статистика сегодня:
🆕 Распарсено: 0 постов
...
```

### 3. Отправьте `/queue`

```
📋 Очередь пуста

Нет постов, ожидающих одобрения.
```

### 4. Отправьте `/history`

```
📜 История пуста

Нет обработанных постов.
```

## 🔧 Интеграция с Celery Workers

Когда Celery worker обработает пост, он должен отправить уведомление админу:

```python
from app.bot.keyboards.inline import get_approval_keyboard

async def send_approval_request(bot: Bot, processed_post: ProcessedPost):
    """Отправляет пост на одобрение админу."""
    text = f"""
🆕 *Новый пост готов к одобрению!*

*Заголовок:*
{processed_post.title}

*Текст:*
{processed_post.caption[:200]}...

*Хештеги:*
{processed_post.hashtags}

*Оригинальный автор:* @{processed_post.original_post.author}
*Лайки:* {processed_post.original_post.likes:,}
*Слайдов:* {processed_post.slides_count}
"""
    
    keyboard = get_approval_keyboard(processed_post.id)
    
    await bot.send_message(
        config.ADMIN_CHAT_ID,
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
```

## 🛠️ TODO (Следующие шаги)

### Высокий приоритет

- [ ] Реализовать FSM для редактирования caption
- [ ] Реализовать FSM для редактирования hashtags
- [ ] Добавить команду `/parse <username>` для ручного парсинга
- [ ] Интегрировать отправку уведомлений из Celery workers

### Средний приоритет

- [ ] Добавить предпросмотр изображений в очереди
- [ ] Добавить фильтры в `/history` (по статусу, дате)
- [ ] Добавить экспорт истории в CSV
- [ ] Добавить команду `/stats` с графиками

### Низкий приоритет

- [ ] Добавить multi-admin поддержку
- [ ] Добавить роли (admin, moderator)
- [ ] Добавить планировщик публикаций
- [ ] Добавить A/B тестирование постов

## 📝 Примеры использования

### Одобрение поста

1. Бот присылает уведомление о новом посте
2. Админ нажимает "✅ Одобрить"
3. Пост меняет статус на `APPROVED`
4. Celery worker публикует пост в Instagram

### Редактирование поста (TODO)

1. Админ нажимает "✏️ Редактировать текст"
2. Бот переходит в состояние `ApprovalStates.editing_caption`
3. Админ отправляет новый текст
4. Бот обновляет caption в БД
5. Бот снова показывает пост с кнопками одобрения

### Просмотр очереди

1. Админ отправляет `/queue`
2. Бот показывает первые 5 постов
3. Админ листает страницы кнопками ⬅️ ➡️
4. Админ может обновить очередь кнопкой 🔄

## 🔒 Безопасность

### Проверка доступа

Все команды проверяют `message.from_user.id == config.ADMIN_CHAT_ID`:

```python
if message.from_user.id != config.ADMIN_CHAT_ID:
    await message.answer("❌ У вас нет доступа к этому боту.")
    return
```

### Логирование

Все действия логируются через `loguru`:

```python
logger.info(f"User {message.from_user.id} started bot")
logger.info(f"Post {post_id} approved by {callback.from_user.id}")
```

### Обработка ошибок

Middleware ловит все ошибки и уведомляет пользователя:

```python
try:
    return await handler(event, data)
except Exception as e:
    logger.error(f"Error in handler: {e}", exc_info=True)
    await event.message.answer("❌ Произошла ошибка. Попробуйте позже.")
```

## 📚 Документация

- [aiogram 3.10 Docs](https://docs.aiogram.dev/en/latest/)
- [FSM States](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html)
- [Inline Keyboards](https://docs.aiogram.dev/en/latest/utils/keyboard.html)
- [Redis Storage](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/storages.html#redis)

## 🐛 Troubleshooting

### Бот не отвечает

1. Проверьте `BOT_TOKEN` в `.env`
2. Проверьте что бот запущен: `python -m app.bot.main`
3. Проверьте логи: `tail -f logs/bot.log`

### Ошибка "У вас нет доступа"

1. Проверьте `ADMIN_CHAT_ID` в `.env`
2. Узнайте свой ID: отправьте `/start` боту @userinfobot

### Ошибка подключения к Redis

1. Проверьте что Redis запущен: `redis-cli ping`
2. Проверьте `REDIS_URL` в `.env`

### Ошибка подключения к БД

1. Проверьте `DATABASE_URL` в `.env`
2. Запустите инициализацию: `python scripts/init_db.py`

## 📊 Метрики

После запуска бота, вы можете отслеживать:

- Количество обработанных команд (логи)
- Время ответа бота (логи)
- Количество ошибок (логи)
- Статус очереди (`/status`)

## 🎯 Best Practices

1. **Всегда проверяйте доступ** - Только ADMIN_CHAT_ID может использовать бота
2. **Логируйте все действия** - Используйте `logger.info()` для важных событий
3. **Обрабатывайте ошибки** - Используйте try/except и уведомляйте пользователя
4. **Используйте async/await** - Все функции должны быть асинхронными
5. **Валидируйте данные** - Проверяйте существование постов перед обработкой

## 🚀 Production Ready

Для production окружения:

1. Используйте PostgreSQL вместо SQLite
2. Настройте connection pooling
3. Добавьте rate limiting
4. Настройте мониторинг (Prometheus + Grafana)
5. Используйте webhook вместо polling
6. Добавьте backup БД

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи: `logs/bot.log`
2. Проверьте статус: `/status`
3. Перезапустите бота: `Ctrl+C` → `python -m app.bot.main`
4. Проверьте документацию: `README.md`
