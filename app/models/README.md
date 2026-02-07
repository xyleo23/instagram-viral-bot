# SQLAlchemy Models

Модели данных для Instagram Viral Bot.

## 📋 Структура

```
app/models/
├── __init__.py           # Экспорты всех моделей
├── base.py              # Базовая настройка SQLAlchemy
├── post.py              # OriginalPost - оригинальные посты
├── processed_post.py    # ProcessedPost - обработанные посты
├── approval.py          # ApprovalHistory - история одобрений
└── README.md            # Эта документация
```

## 🗄️ Модели

### 1. OriginalPost (post.py)

Оригинальные посты из Instagram.

**Поля:**
- `id` - Primary key
- `external_id` - Instagram post ID (уникальный)
- `author` - Instagram username
- `author_url` - URL профиля
- `text` - Полный текст поста
- `likes` - Количество лайков
- `comments` - Количество комментариев
- `engagement` - Коэффициент вовлеченности
- `post_url` - Прямая ссылка на пост
- `posted_at` - Дата создания в Instagram
- `status` - Статус (PostStatus enum)
- `created_at`, `updated_at` - Timestamps

**Статусы (PostStatus):**
- `PARSING` - Только что распарсен
- `FILTERED` - Прошел фильтр (вирусный)
- `PROCESSING` - В обработке AI
- `PROCESSED` - Обработан AI
- `APPROVED` - Одобрен админом
- `REJECTED` - Отклонен админом
- `POSTED` - Опубликован в Instagram

**Методы:**
- `is_viral(min_likes=5000)` - Проверка вирусности
- `days_old()` - Возраст поста в днях
- `is_fresh(max_days=3)` - Проверка свежести
- `to_dict()` - Сериализация в dict

### 2. ProcessedPost (processed_post.py)

Обработанные посты после AI рерайта.

**Поля:**
- `id` - Primary key
- `original_post_id` - FK на OriginalPost
- `title` - Новый заголовок
- `caption` - Переписанный текст
- `hashtags` - Хештеги через пробел
- `slides` - JSON массив текстов для слайдов
- `slides_count` - Количество слайдов
- `ai_model` - Модель AI
- `tokens_used` - Токенов использовано
- `cost_usd` - Стоимость обработки
- `image_urls` - JSON массив URLs изображений
- `yandex_disk_folder` - Путь на Яндекс.Диске
- `status` - Статус (ProcessedStatus enum)
- `created_at`, `updated_at` - Timestamps

**Статусы (ProcessedStatus):**
- `PENDING_APPROVAL` - Ждет одобрения
- `APPROVED` - Одобрен
- `REJECTED` - Отклонен
- `POSTED` - Опубликован

**Методы:**
- `get_full_caption()` - Полный caption для Instagram
- `get_telegram_preview(max_length=300)` - Короткий превью
- `to_dict()` - Сериализация в dict

### 3. ApprovalHistory (approval.py)

История одобрений/отклонений постов.

**Поля:**
- `id` - Primary key
- `processed_post_id` - FK на ProcessedPost
- `user_id` - Telegram User ID
- `username` - Telegram username
- `decision` - Решение (DecisionType enum)
- `comment` - Комментарий админа
- `timestamp` - Время решения

**Решения (DecisionType):**
- `APPROVED` - Одобрено
- `REJECTED` - Отклонено
- `EDITED` - Отредактировано

**Методы:**
- `get_latest_for_post(session, post_id)` - Последнее решение
- `is_approved()` - Проверка одобрения
- `to_dict()` - Сериализация в dict

## 🚀 Использование

### Инициализация БД

```python
from app.models import init_db, create_tables

# Инициализация подключения
init_db("postgresql+asyncpg://user:pass@localhost/dbname")

# Создание таблиц
await create_tables()
```

### Работа с сессией

```python
from app.models import get_session

async with get_session() as session:
    # Ваш код здесь
    result = await session.execute(select(OriginalPost))
    posts = result.scalars().all()
```

### Создание поста

```python
from app.models import OriginalPost, PostStatus
from datetime import datetime

async with get_session() as session:
    post = OriginalPost(
        external_id="123456789",
        author="username",
        author_url="https://instagram.com/username",
        text="Post text...",
        likes=10000,
        comments=500,
        engagement=0.05,
        post_url="https://instagram.com/p/123456789",
        posted_at=datetime.utcnow(),
        status=PostStatus.PARSING
    )
    session.add(post)
    await session.commit()
```

### Запросы

```python
from sqlalchemy import select
from app.models import OriginalPost, PostStatus

# Получить все вирусные посты
async with get_session() as session:
    result = await session.execute(
        select(OriginalPost)
        .where(OriginalPost.status == PostStatus.FILTERED)
        .where(OriginalPost.likes >= 5000)
        .order_by(OriginalPost.likes.desc())
    )
    posts = result.scalars().all()

# Получить пост по external_id
async with get_session() as session:
    result = await session.execute(
        select(OriginalPost)
        .where(OriginalPost.external_id == "123456789")
    )
    post = result.scalar_one_or_none()
```

### Обновление статуса

```python
from app.models import OriginalPost, PostStatus

async with get_session() as session:
    result = await session.execute(
        select(OriginalPost).where(OriginalPost.id == 1)
    )
    post = result.scalar_one()
    post.status = PostStatus.APPROVED
    await session.commit()
```

## 🔗 Связи (Relations)

```
OriginalPost (1) ──< (N) ProcessedPost (1) ──< (N) ApprovalHistory
```

- Один `OriginalPost` может иметь несколько `ProcessedPost` (разные варианты обработки)
- Один `ProcessedPost` может иметь несколько `ApprovalHistory` (история изменений)

### Использование связей

```python
# Получить все обработанные версии поста
async with get_session() as session:
    result = await session.execute(
        select(OriginalPost)
        .where(OriginalPost.id == 1)
        .options(selectinload(OriginalPost.processed_posts))
    )
    original_post = result.scalar_one()
    for processed in original_post.processed_posts:
        print(processed.title)

# Получить историю одобрений
async with get_session() as session:
    result = await session.execute(
        select(ProcessedPost)
        .where(ProcessedPost.id == 1)
        .options(selectinload(ProcessedPost.approvals))
    )
    processed = result.scalar_one()
    for approval in processed.approvals:
        print(f"{approval.decision.value} by {approval.username}")
```

## 📊 Индексы

Для оптимизации запросов созданы следующие индексы:

**OriginalPost:**
- `external_id` (unique)
- `author`
- `likes`
- `status`
- `idx_author_likes` (composite: author + likes DESC)
- `idx_status_created` (composite: status + created_at DESC)

**ProcessedPost:**
- `original_post_id` (FK)
- `status`

**ApprovalHistory:**
- `processed_post_id` (FK)
- `user_id`
- `decision`
- `timestamp`

## 🛠️ Скрипты

### Инициализация БД

```bash
python scripts/init_db.py
```

### Проверка таблиц (PostgreSQL)

```bash
psql -U instagram_bot -d instagram_viral -c "\dt"
```

## 📝 TODO

- [ ] Добавить модель `Author` для хранения информации об авторах
- [ ] Добавить модель `PublishSchedule` для расписания публикаций
- [ ] Добавить модель `GoogleSheetsSync` для синхронизации с Google Sheets
- [ ] Создать Alembic миграции
- [ ] Добавить soft delete (deleted_at)
- [ ] Добавить полнотекстовый поиск
