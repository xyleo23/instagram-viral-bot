# 🗄️ Database Schema

Схема базы данных Instagram Viral Bot.

## 📊 ER Диаграмма

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORIGINAL_POSTS                            │
├─────────────────────────────────────────────────────────────────┤
│ PK  id                    INTEGER                                │
│ UK  external_id           VARCHAR(100)    [Instagram post ID]    │
│     author                VARCHAR(100)    [Instagram username]   │
│     author_url            VARCHAR(255)                           │
│     text                  TEXT                                   │
│     likes                 INTEGER         [indexed]              │
│     comments              INTEGER                                │
│     engagement            FLOAT                                  │
│     post_url              VARCHAR(500)                           │
│     posted_at             TIMESTAMP                              │
│     status                ENUM            [indexed]              │
│     created_at            TIMESTAMP       [auto]                 │
│     updated_at            TIMESTAMP       [auto]                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PROCESSED_POSTS                            │
├─────────────────────────────────────────────────────────────────┤
│ PK  id                    INTEGER                                │
│ FK  original_post_id      INTEGER         [CASCADE DELETE]       │
│     title                 VARCHAR(200)                           │
│     caption               TEXT                                   │
│     hashtags              VARCHAR(500)                           │
│     slides                JSON            [array of strings]     │
│     slides_count          INTEGER                                │
│     ai_model              VARCHAR(100)                           │
│     tokens_used           INTEGER                                │
│     cost_usd              FLOAT                                  │
│     image_urls            JSON            [array of strings]     │
│     yandex_disk_folder    VARCHAR(500)    [nullable]             │
│     status                ENUM            [indexed]              │
│     created_at            TIMESTAMP       [auto]                 │
│     updated_at            TIMESTAMP       [auto]                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APPROVAL_HISTORY                            │
├─────────────────────────────────────────────────────────────────┤
│ PK  id                    INTEGER                                │
│ FK  processed_post_id     INTEGER         [CASCADE DELETE]       │
│     user_id               INTEGER         [Telegram User ID]     │
│     username              VARCHAR(100)    [Telegram username]    │
│     decision              ENUM            [indexed]              │
│     comment               TEXT            [nullable]             │
│     timestamp             TIMESTAMP       [indexed]              │
└─────────────────────────────────────────────────────────────────┘
```

## 🔑 Ключи и индексы

### ORIGINAL_POSTS

**Primary Key:**
- `id` (auto-increment)

**Unique Keys:**
- `external_id` (Instagram post ID)

**Indexes:**
- `external_id` (unique)
- `author`
- `likes`
- `status`
- `idx_author_likes` (composite: author, likes DESC)
- `idx_status_created` (composite: status, created_at DESC)

**Foreign Keys:**
- None

### PROCESSED_POSTS

**Primary Key:**
- `id` (auto-increment)

**Indexes:**
- `original_post_id`
- `status`

**Foreign Keys:**
- `original_post_id` → `original_posts.id` (CASCADE DELETE)

### APPROVAL_HISTORY

**Primary Key:**
- `id` (auto-increment)

**Indexes:**
- `processed_post_id`
- `user_id`
- `decision`
- `timestamp`

**Foreign Keys:**
- `processed_post_id` → `processed_posts.id` (CASCADE DELETE)

## 📋 Enums

### PostStatus (original_posts.status)

```python
PARSING      # Только что распарсен
FILTERED     # Прошел фильтр (вирусный)
PROCESSING   # В обработке AI
PROCESSED    # Обработан AI
APPROVED     # Одобрен админом
REJECTED     # Отклонен админом
POSTED       # Опубликован в Instagram
```

### ProcessedStatus (processed_posts.status)

```python
PENDING_APPROVAL  # Ждет одобрения
APPROVED          # Одобрен
REJECTED          # Отклонен
POSTED            # Опубликован
```

### DecisionType (approval_history.decision)

```python
APPROVED  # Одобрено
REJECTED  # Отклонено
EDITED    # Отредактировано
```

## 🔄 Жизненный цикл данных

### 1. Парсинг Instagram

```
Instagram API
    ↓
OriginalPost (status: PARSING)
    ↓
Фильтрация (likes >= 5000, age <= 3 days)
    ↓
OriginalPost (status: FILTERED)
```

### 2. AI обработка

```
OriginalPost (status: FILTERED)
    ↓
OpenRouter API (AI rewrite)
    ↓
OriginalPost (status: PROCESSING)
    ↓
ProcessedPost (status: PENDING_APPROVAL)
    ↓
OriginalPost (status: PROCESSED)
```

### 3. Одобрение админом

```
ProcessedPost (status: PENDING_APPROVAL)
    ↓
Telegram Bot → Admin
    ↓
Admin Decision (approve/reject)
    ↓
ApprovalHistory (decision: APPROVED/REJECTED)
    ↓
ProcessedPost (status: APPROVED/REJECTED)
    ↓
OriginalPost (status: APPROVED/REJECTED)
```

### 4. Генерация карусели

```
ProcessedPost (status: APPROVED)
    ↓
Orshot API (generate images)
    ↓
ProcessedPost.image_urls = [...]
    ↓
Yandex.Disk (upload)
    ↓
ProcessedPost.yandex_disk_folder = "..."
```

### 5. Публикация

```
ProcessedPost (status: APPROVED)
    ↓
Instagram API (publish)
    ↓
ProcessedPost (status: POSTED)
    ↓
OriginalPost (status: POSTED)
```

## 📊 Примеры запросов

### Получить все вирусные посты за последние 3 дня

```python
from sqlalchemy import select, and_
from datetime import datetime, timedelta

three_days_ago = datetime.utcnow() - timedelta(days=3)

async with get_session() as session:
    result = await session.execute(
        select(OriginalPost)
        .where(
            and_(
                OriginalPost.status == PostStatus.FILTERED,
                OriginalPost.likes >= 5000,
                OriginalPost.posted_at >= three_days_ago
            )
        )
        .order_by(OriginalPost.likes.desc())
    )
    posts = result.scalars().all()
```

### Получить все посты, ожидающие одобрения

```python
async with get_session() as session:
    result = await session.execute(
        select(ProcessedPost)
        .where(ProcessedPost.status == ProcessedStatus.PENDING_APPROVAL)
        .order_by(ProcessedPost.created_at.desc())
    )
    posts = result.scalars().all()
```

### Получить историю одобрений для пользователя

```python
async with get_session() as session:
    result = await session.execute(
        select(ApprovalHistory)
        .where(ApprovalHistory.user_id == telegram_user_id)
        .order_by(ApprovalHistory.timestamp.desc())
        .limit(10)
    )
    history = result.scalars().all()
```

### Получить пост со всеми связями

```python
from sqlalchemy.orm import selectinload

async with get_session() as session:
    result = await session.execute(
        select(OriginalPost)
        .where(OriginalPost.id == post_id)
        .options(
            selectinload(OriginalPost.processed_posts)
            .selectinload(ProcessedPost.approvals)
        )
    )
    post = result.scalar_one()
    
    # Теперь можно обращаться без дополнительных запросов
    for processed in post.processed_posts:
        print(f"Title: {processed.title}")
        for approval in processed.approvals:
            print(f"  - {approval.decision.value} by {approval.username}")
```

### Статистика по авторам

```python
from sqlalchemy import func

async with get_session() as session:
    result = await session.execute(
        select(
            OriginalPost.author,
            func.count(OriginalPost.id).label('posts_count'),
            func.avg(OriginalPost.likes).label('avg_likes'),
            func.max(OriginalPost.likes).label('max_likes')
        )
        .group_by(OriginalPost.author)
        .order_by(func.count(OriginalPost.id).desc())
    )
    stats = result.all()
```

### Посты с наибольшей стоимостью обработки

```python
async with get_session() as session:
    result = await session.execute(
        select(ProcessedPost)
        .order_by(ProcessedPost.cost_usd.desc())
        .limit(10)
    )
    expensive_posts = result.scalars().all()
```

## 🔒 Constraints

### NOT NULL

- Все основные поля (кроме `comment`, `username`, `yandex_disk_folder`)
- Timestamps (created_at, updated_at, timestamp)

### UNIQUE

- `original_posts.external_id` - предотвращает дубликаты постов

### CASCADE DELETE

- При удалении `OriginalPost` → удаляются все `ProcessedPost`
- При удалении `ProcessedPost` → удаляются все `ApprovalHistory`

### DEFAULT VALUES

```python
# OriginalPost
comments = 0
engagement = 0.0
status = PostStatus.PARSING

# ProcessedPost
tokens_used = 0
cost_usd = 0.0
status = ProcessedStatus.PENDING_APPROVAL

# ApprovalHistory
timestamp = datetime.utcnow()
```

## 📈 Оптимизация

### Индексы для частых запросов

1. **Поиск по автору и лайкам:**
   ```sql
   CREATE INDEX idx_author_likes ON original_posts (author, likes DESC);
   ```

2. **Поиск по статусу и дате:**
   ```sql
   CREATE INDEX idx_status_created ON original_posts (status, created_at DESC);
   ```

3. **Поиск по FK:**
   ```sql
   CREATE INDEX idx_original_post_id ON processed_posts (original_post_id);
   CREATE INDEX idx_processed_post_id ON approval_history (processed_post_id);
   ```

### Connection Pooling

```python
engine = create_async_engine(
    database_url,
    pool_size=10,        # Основной пул
    max_overflow=20,     # Дополнительные соединения
    pool_pre_ping=True,  # Проверка соединения
    pool_recycle=3600    # Переподключение каждый час
)
```

### Eager Loading

Используйте `selectinload` для загрузки связей:

```python
.options(selectinload(OriginalPost.processed_posts))
```

## 🛡️ Безопасность

### SQL Injection Protection

SQLAlchemy автоматически экранирует параметры:

```python
# Безопасно
result = await session.execute(
    select(OriginalPost).where(OriginalPost.author == user_input)
)
```

### Транзакции

Все операции в `get_session()` автоматически в транзакции:

```python
async with get_session() as session:
    # Все операции в транзакции
    session.add(post)
    # Автоматический commit при выходе
    # Автоматический rollback при ошибке
```

## 📝 Миграции

### Создание миграции

```bash
alembic revision --autogenerate -m "Initial schema"
```

### Применение миграции

```bash
alembic upgrade head
```

### Откат миграции

```bash
alembic downgrade -1
```

## 🎯 Best Practices

1. **Всегда используйте async/await**
2. **Используйте context manager для сессий**
3. **Добавляйте индексы для часто используемых полей**
4. **Используйте Enums для статусов**
5. **Валидируйте данные перед сохранением**
6. **Используйте транзакции для критичных операций**
7. **Логируйте все изменения статусов**
8. **Делайте backup перед миграциями**

## 📚 Дополнительно

- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)
- [Database Indexing](https://use-the-index-luke.com/)
