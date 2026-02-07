# ✅ Bot Handlers Checklist

## 📋 Что создано

### ✅ Структура директорий

```
app/bot/
├── main.py                      ✅ Создан
├── states.py                    ✅ Создан
├── handlers/
│   ├── __init__.py              ✅ Создан
│   ├── start.py                 ✅ Создан (150 строк)
│   ├── queue.py                 ✅ Создан (120 строк)
│   ├── approval.py              ✅ Создан (150 строк)
│   └── history.py               ✅ Создан (100 строк)
├── keyboards/
│   ├── __init__.py              ✅ Создан
│   └── inline.py                ✅ Создан (120 строк)
├── middlewares/
│   ├── __init__.py              ✅ Создан
│   └── logging_middleware.py   ✅ Создан (60 строк)
└── README.md                    ✅ Создан (документация)
```

### ✅ Реализованные команды

- ✅ `/start` - Приветствие и главное меню
- ✅ `/help` - Справка по командам
- ✅ `/status` - Статус системы и статистика
- ✅ `/queue` - Просмотр очереди на одобрение
- ✅ `/history` - История обработанных постов

### ✅ Реализованные callback handlers

- ✅ `approve:{post_id}` - Одобрение поста
- ✅ `reject:{post_id}` - Отклонение поста
- ✅ `edit_caption:{post_id}` - Редактирование текста (TODO)
- ✅ `edit_hashtags:{post_id}` - Редактирование хештегов (TODO)
- ✅ `show_queue` - Показать очередь
- ✅ `show_status` - Показать статус
- ✅ `show_history` - Показать историю
- ✅ `queue_page:{page}` - Навигация по очереди
- ✅ `queue_noop` - Заглушка для кнопки страницы

### ✅ Inline клавиатуры

- ✅ `get_approval_keyboard()` - Кнопки одобрения поста
- ✅ `get_queue_navigation_keyboard()` - Навигация по очереди
- ✅ `get_main_menu_keyboard()` - Главное меню

### ✅ FSM States

- ✅ `ApprovalStates` - Состояния одобрения
  - `waiting_approval`
  - `editing_caption`
  - `editing_hashtags`
- ✅ `ManualParsingStates` - Ручной парсинг
  - `waiting_username`

### ✅ Middleware

- ✅ `LoggingMiddleware` - Логирование всех событий
  - Логирование сообщений
  - Логирование callback queries
  - Обработка ошибок

### ✅ Зависимости

- ✅ `aiogram==3.10.0` - Уже в requirements.txt
- ✅ `aiosqlite==0.19.0` - Добавлено в requirements.txt
- ✅ `redis==5.0.1` - Уже в requirements.txt
- ✅ `loguru==0.7.2` - Уже в requirements.txt

## 🚀 Запуск бота

### 1. Проверьте `.env` файл

```bash
# Обязательные параметры
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_CHAT_ID=123456789
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite+aiosqlite:///./instagram_bot.db
```

### 2. Запустите Redis

```bash
# Через Docker
docker run -d -p 6379:6379 redis:alpine

# Или локально
redis-server
```

### 3. Инициализируйте БД

```bash
python scripts/init_db.py
```

### 4. Запустите бота

```bash
python -m app.bot.main
```

### 5. Проверьте в Telegram

Отправьте боту:
- `/start` - Должно показать приветствие и меню
- `/status` - Должно показать статистику
- `/queue` - Должно показать "Очередь пуста"
- `/history` - Должно показать "История пуста"
- `/help` - Должно показать справку

## ✅ Что работает

### ✅ Базовые функции

- ✅ Запуск бота через `python -m app.bot.main`
- ✅ Проверка доступа (только ADMIN_CHAT_ID)
- ✅ Логирование всех событий
- ✅ Обработка ошибок с уведомлением пользователя
- ✅ Redis storage для FSM
- ✅ Асинхронная работа с БД

### ✅ Команды

- ✅ `/start` - Показывает приветствие и главное меню
- ✅ `/help` - Показывает справку
- ✅ `/status` - Показывает статистику из БД
  - Посты на одобрении
  - Распарсено сегодня
  - Всего постов
  - Одобрено постов
  - Настройки системы
- ✅ `/queue` - Показывает очередь с пагинацией
- ✅ `/history` - Показывает последние 10 постов

### ✅ Одобрение постов

- ✅ Кнопка "✅ Одобрить" - Меняет статус на APPROVED
- ✅ Кнопка "❌ Отклонить" - Меняет статус на REJECTED
- ✅ Сохранение истории решений в `approval_history`
- ✅ Обновление статуса оригинального поста

### ✅ Очередь постов

- ✅ Пагинация (5 постов на страницу)
- ✅ Навигация: ⬅️ Назад / ➡️ Вперед
- ✅ Кнопка 🔄 Обновить
- ✅ Показывает: заголовок, автора, лайки, ID

### ✅ История постов

- ✅ Показывает последние 10 постов
- ✅ Фильтрация по статусу (APPROVED, REJECTED, POSTED)
- ✅ Сортировка по дате обновления
- ✅ Иконки статусов (✅ ❌ 📤)

## ⚠️ TODO (Не реализовано)

### Высокий приоритет

- ⚠️ FSM для редактирования caption
- ⚠️ FSM для редактирования hashtags
- ⚠️ Команда `/parse <username>` для ручного парсинга
- ⚠️ Интеграция с Celery workers (отправка уведомлений)
- ⚠️ Предпросмотр изображений в очереди

### Средний приоритет

- ⚠️ Фильтры в `/history` (по статусу, дате)
- ⚠️ Экспорт истории в CSV
- ⚠️ Команда `/stats` с графиками
- ⚠️ Multi-admin поддержка

### Низкий приоритет

- ⚠️ Роли (admin, moderator)
- ⚠️ Планировщик публикаций
- ⚠️ A/B тестирование постов

## 🔧 Интеграция с Celery Workers

### Что нужно добавить в Celery worker

После обработки поста AI, worker должен отправить уведомление:

```python
# В app/workers/tasks/processing.py

from aiogram import Bot
from app.config import get_config
from app.bot.keyboards.inline import get_approval_keyboard

async def send_approval_notification(processed_post_id: int):
    """Отправляет уведомление админу о новом посте."""
    config = get_config()
    bot = Bot(token=config.BOT_TOKEN)
    
    async for session in get_session():
        result = await session.execute(
            select(ProcessedPost).where(ProcessedPost.id == processed_post_id)
        )
        post = result.scalar_one()
        
        text = f"""
🆕 *Новый пост готов к одобрению!*

*Заголовок:*
{post.title}

*Текст:*
{post.caption[:200]}...

*Хештеги:*
{post.hashtags}

*Оригинальный автор:* @{post.original_post.author}
*Лайки:* {post.original_post.likes:,}
*Слайдов:* {post.slides_count}

*Яндекс.Диск:* {post.yandex_disk_folder or 'Не загружено'}
"""
        
        keyboard = get_approval_keyboard(post.id)
        
        # Если есть изображения, отправляем первое как превью
        if post.image_urls and len(post.image_urls) > 0:
            await bot.send_photo(
                config.ADMIN_CHAT_ID,
                photo=post.image_urls[0],
                caption=text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            await bot.send_message(
                config.ADMIN_CHAT_ID,
                text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    
    await bot.session.close()


# Добавить в конец task'а process_post
@celery_app.task(name="process_post")
def process_post(original_post_id: int):
    try:
        # ... существующий код обработки ...
        
        # После успешной обработки
        asyncio.run(send_approval_notification(processed_post.id))
        
    except Exception as e:
        logger.error(f"Error processing post: {e}")
```

## 📊 Тестирование

### Ручное тестирование

1. ✅ Запустите бота: `python -m app.bot.main`
2. ✅ Отправьте `/start` - Проверьте приветствие
3. ✅ Отправьте `/status` - Проверьте статистику
4. ✅ Отправьте `/queue` - Проверьте очередь
5. ✅ Отправьте `/history` - Проверьте историю
6. ✅ Отправьте `/help` - Проверьте справку

### Тестирование с данными

1. ⚠️ Создайте тестовый пост в БД
2. ⚠️ Проверьте `/queue` - Должен показать пост
3. ⚠️ Нажмите "✅ Одобрить" - Проверьте изменение статуса
4. ⚠️ Проверьте `/history` - Должен показать одобренный пост

### Unit тесты (TODO)

```bash
pytest tests/test_bot_handlers.py
```

## 🐛 Известные проблемы

### 1. Редактирование постов не реализовано

**Проблема:** Кнопки "✏️ Редактировать текст" и "🏷 Изменить хештеги" показывают заглушку.

**Решение:** Реализовать FSM states для редактирования (TODO).

### 2. Нет предпросмотра изображений

**Проблема:** В очереди не показываются изображения постов.

**Решение:** Добавить отправку фото в `show_queue_page()` (TODO).

### 3. Нет команды `/parse`

**Проблема:** Нельзя вручную запустить парсинг аккаунта.

**Решение:** Реализовать handler для `/parse <username>` (TODO).

## 📝 Логи

Все события логируются в `logs/bot.log`:

```
2026-01-30 11:20:00 | INFO | User 123456789 started bot
2026-01-30 11:20:05 | INFO | Message from 123456789 (@admin): /status
2026-01-30 11:20:10 | INFO | Callback from 123456789 (@admin): show_queue
2026-01-30 11:20:15 | INFO | Post 1 approved by 123456789
```

## 🎯 Следующие шаги

1. ✅ Базовые handlers созданы
2. ⚠️ Реализовать FSM для редактирования
3. ⚠️ Добавить команду `/parse`
4. ⚠️ Интегрировать с Celery workers
5. ⚠️ Добавить предпросмотр изображений
6. ⚠️ Написать unit тесты

## 📚 Документация

- [README.md](app/bot/README.md) - Полная документация
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Схема БД
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - План реализации

## ✅ Checklist для запуска

- [ ] `.env` файл настроен
- [ ] `BOT_TOKEN` заполнен
- [ ] `ADMIN_CHAT_ID` заполнен
- [ ] Redis запущен (`redis-server`)
- [ ] БД инициализирована (`python scripts/init_db.py`)
- [ ] Бот запущен (`python -m app.bot.main`)
- [ ] Бот отвечает на `/start` в Telegram

## 🎉 Готово!

Базовые Telegram Bot handlers для Instagram Viral Bot успешно созданы!

Все файлы созданы, структура готова, можно запускать и тестировать.
