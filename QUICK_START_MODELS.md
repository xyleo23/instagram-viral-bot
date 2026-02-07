# 🚀 Quick Start - SQLAlchemy Models

Быстрый старт для работы с моделями базы данных.

## ⚡ За 5 минут

### 1. Установка зависимостей

```bash
cd instagram_bot
pip install -r requirements.txt
```

### 2. Настройка .env

Создайте `.env` файл:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://instagram_bot:password@localhost/instagram_viral

# Telegram Bot
BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_ID=123456789

# OpenRouter (для AI)
OPENROUTER_API_KEY=your_key_here

# Orshot (для изображений)
ORSHOT_API_KEY=your_key_here
```

### 3. Инициализация БД

```bash
python scripts/init_db.py
```

Вывод:
```
🔧 Initializing database...
📍 Database URL: postgresql+asyncpg://...
✅ Database initialized successfully!

Created tables:
  - original_posts
  - processed_posts
  - approval_history
```

### 4. Тестирование

```bash
python scripts/test_models.py
```

### 5. Проверка в PostgreSQL

```bash
psql -U instagram_bot -d instagram_viral -c "\dt"
```

## 📝 Базовое использование

### Импорты

```python
from app.models import (
    init_db,
    get_session,
    OriginalPost,
    PostStatus,
    ProcessedPost,
    ProcessedStatus,
    ApprovalHistory,
    DecisionType,
)
```

### Инициализация

```python
from app.config import get_config

config = get_config()
init_db(config.get_database_url())
```

### Создание поста

```python
from datetime import datetime

async with get_session() as session:
    post = OriginalPost(
        external_id="123456",
        author="username",
        author_url="https://instagram.com/username",
        text="Post text...",
        likes=10000,
        comments=500,
        engagement=0.05,
        post_url="https://instagram.com/p/123456",
        posted_at=datetime.utcnow(),
        status=PostStatus.PARSING
    )
    session.add(post)
    await session.commit()
    print(f"Created post with id={post.id}")
```

### Чтение постов

```python
from sqlalchemy import select

async with get_session() as session:
    # Все вирусные посты
    result = await session.execute(
        select(OriginalPost)
        .where(OriginalPost.likes >= 5000)
        .order_by(OriginalPost.likes.desc())
    )
    posts = result.scalars().all()
    
    # Один пост по ID
    result = await session.execute(
        select(OriginalPost).where(OriginalPost.id == 1)
    )
    post = result.scalar_one()
```

### Обновление статуса

```python
async with get_session() as session:
    result = await session.execute(
        select(OriginalPost).where(OriginalPost.id == 1)
    )
    post = result.scalar_one()
    post.status = PostStatus.APPROVED
    await session.commit()
```

### Удаление

```python
async with get_session() as session:
    result = await session.execute(
        select(OriginalPost).where(OriginalPost.id == 1)
    )
    post = result.scalar_one()
    await session.delete(post)
    await session.commit()
```

## 🎯 Типичные сценарии

### Сценарий 1: Сохранение распарсенного поста

```python
async def save_parsed_post(post_data: dict):
    """Сохранить пост из Instagram."""
    async with get_session() as session:
        # Проверить, не существует ли уже
        result = await session.execute(
            select(OriginalPost)
            .where(OriginalPost.external_id == post_data['id'])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Post {post_data['id']} already exists")
            return existing
        
        # Создать новый
        post = OriginalPost(
            external_id=post_data['id'],
            author=post_data['username'],
            author_url=f"https://instagram.com/{post_data['username']}",
            text=post_data['caption'],
            likes=post_data['likes'],
            comments=post_data['comments'],
            engagement=post_data.get('engagement', 0.0),
            post_url=post_data['url'],
            posted_at=post_data['timestamp'],
            status=PostStatus.PARSING
        )
        session.add(post)
        await session.commit()
        
        # Проверить вирусность
        if post.is_viral():
            post.status = PostStatus.FILTERED
            await session.commit()
            print(f"✅ Viral post saved: {post.likes} likes")
        
        return post
```

### Сценарий 2: Обработка AI

```python
async def process_with_ai(original_post_id: int, ai_response: dict):
    """Сохранить результат AI обработки."""
    async with get_session() as session:
        # Обновить статус оригинального поста
        result = await session.execute(
            select(OriginalPost).where(OriginalPost.id == original_post_id)
        )
        original = result.scalar_one()
        original.status = PostStatus.PROCESSING
        
        # Создать обработанную версию
        processed = ProcessedPost(
            original_post_id=original_post_id,
            title=ai_response['title'],
            caption=ai_response['caption'],
            hashtags=' '.join(ai_response['hashtags']),
            slides=ai_response['slides'],
            slides_count=len(ai_response['slides']),
            ai_model=ai_response['model'],
            tokens_used=ai_response['tokens'],
            cost_usd=ai_response['cost'],
            image_urls=[],
            status=ProcessedStatus.PENDING_APPROVAL
        )
        session.add(processed)
        
        # Обновить статус
        original.status = PostStatus.PROCESSED
        
        await session.commit()
        print(f"✅ Post processed: {processed.title}")
        
        return processed
```

### Сценарий 3: Одобрение поста

```python
async def approve_post(processed_post_id: int, user_id: int, username: str):
    """Одобрить пост."""
    async with get_session() as session:
        # Получить пост
        result = await session.execute(
            select(ProcessedPost).where(ProcessedPost.id == processed_post_id)
        )
        processed = result.scalar_one()
        
        # Обновить статус
        processed.status = ProcessedStatus.APPROVED
        
        # Создать запись в истории
        approval = ApprovalHistory(
            processed_post_id=processed_post_id,
            user_id=user_id,
            username=username,
            decision=DecisionType.APPROVED,
            timestamp=datetime.utcnow()
        )
        session.add(approval)
        
        # Обновить оригинальный пост
        result = await session.execute(
            select(OriginalPost).where(OriginalPost.id == processed.original_post_id)
        )
        original = result.scalar_one()
        original.status = PostStatus.APPROVED
        
        await session.commit()
        print(f"✅ Post approved by @{username}")
```

### Сценарий 4: Получение постов для обработки

```python
async def get_posts_to_process(limit: int = 10):
    """Получить посты, готовые к AI обработке."""
    async with get_session() as session:
        result = await session.execute(
            select(OriginalPost)
            .where(OriginalPost.status == PostStatus.FILTERED)
            .order_by(OriginalPost.likes.desc())
            .limit(limit)
        )
        posts = result.scalars().all()
        
        print(f"Found {len(posts)} posts to process")
        return posts
```

### Сценарий 5: Статистика

```python
from sqlalchemy import func

async def get_statistics():
    """Получить общую статистику."""
    async with get_session() as session:
        # Количество постов по статусам
        result = await session.execute(
            select(
                OriginalPost.status,
                func.count(OriginalPost.id)
            )
            .group_by(OriginalPost.status)
        )
        status_counts = dict(result.all())
        
        # Общая стоимость обработки
        result = await session.execute(
            select(func.sum(ProcessedPost.cost_usd))
        )
        total_cost = result.scalar() or 0.0
        
        # Средний engagement
        result = await session.execute(
            select(func.avg(OriginalPost.engagement))
        )
        avg_engagement = result.scalar() or 0.0
        
        return {
            'status_counts': status_counts,
            'total_cost': total_cost,
            'avg_engagement': avg_engagement
        }
```

## 📚 Дополнительные примеры

Смотрите файл `examples/models_usage.py` для более подробных примеров:

```bash
python examples/models_usage.py
```

## 📖 Документация

- **app/models/README.md** - Полная документация по моделям
- **DATABASE_SCHEMA.md** - Схема базы данных
- **scripts/MIGRATIONS.md** - Руководство по миграциям
- **MODELS_CREATED.md** - Отчет о созданных моделях

## 🔧 Полезные команды

### PostgreSQL

```bash
# Подключиться к БД
psql -U instagram_bot -d instagram_viral

# Список таблиц
\dt

# Структура таблицы
\d original_posts

# Количество записей
SELECT COUNT(*) FROM original_posts;

# Посты по статусам
SELECT status, COUNT(*) FROM original_posts GROUP BY status;
```

### Python

```bash
# Инициализация БД
python scripts/init_db.py

# Тесты
python scripts/test_models.py

# Примеры использования
python examples/models_usage.py

# Запуск бота
python -m app.main
```

## ❓ FAQ

### Как изменить структуру таблицы?

1. Измените модель в `app/models/`
2. Создайте миграцию: `alembic revision --autogenerate -m "Description"`
3. Примените: `alembic upgrade head`

### Как сбросить БД?

```python
from app.models import init_db, drop_tables, create_tables
from app.config import get_config

config = get_config()
init_db(config.get_database_url())

# Удалить все таблицы
await drop_tables()

# Создать заново
await create_tables()
```

### Как добавить индекс?

```python
from sqlalchemy import Index

# В модели
Index("idx_custom", OriginalPost.field1, OriginalPost.field2)
```

### Как сделать backup?

```bash
pg_dump -U instagram_bot instagram_viral > backup.sql
```

### Как восстановить из backup?

```bash
psql -U instagram_bot instagram_viral < backup.sql
```

## 🎉 Готово!

Теперь вы можете работать с моделями базы данных!

Следующие шаги:
1. Интегрируйте модели в сервисы (`app/services/`)
2. Обновите handlers (`app/handlers/`)
3. Добавьте логирование операций с БД
4. Настройте мониторинг производительности

Удачи! 🚀
