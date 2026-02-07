# ✅ SQLAlchemy Models - Completed

Все модели для Instagram Viral Bot успешно созданы!

## 📦 Созданные файлы

### 🗄️ Модели (app/models/)

| Файл | Строк | Описание |
|------|-------|----------|
| `base.py` | 97 | Базовая настройка SQLAlchemy, engine, sessions |
| `post.py` | 143 | OriginalPost модель + PostStatus enum |
| `processed_post.py` | 147 | ProcessedPost модель + ProcessedStatus enum |
| `approval.py` | 108 | ApprovalHistory модель + DecisionType enum |
| `__init__.py` | 23 | Экспорты всех моделей |
| `README.md` | - | Документация по моделям |

**Итого:** 518 строк кода

### 🛠️ Скрипты (scripts/)

| Файл | Описание |
|------|----------|
| `init_db.py` | Инициализация БД и создание таблиц |
| `test_models.py` | Тестовый скрипт для проверки моделей |
| `MIGRATIONS.md` | Руководство по миграциям |

## 🗂️ Структура БД

### Таблицы

1. **original_posts** - Оригинальные посты из Instagram
   - 12 полей + timestamps
   - 7 статусов (PARSING → POSTED)
   - Индексы: external_id, author, likes, status
   - Composite индексы: author+likes, status+created_at

2. **processed_posts** - Обработанные AI посты
   - 13 полей + timestamps
   - 4 статуса (PENDING_APPROVAL → POSTED)
   - JSON поля: slides, image_urls
   - FK: original_post_id (CASCADE DELETE)

3. **approval_history** - История одобрений
   - 7 полей + timestamp
   - 3 типа решений (APPROVED, REJECTED, EDITED)
   - FK: processed_post_id (CASCADE DELETE)

### Связи

```
OriginalPost (1) ──< (N) ProcessedPost (1) ──< (N) ApprovalHistory
```

## 🎯 Возможности

### Модель OriginalPost

```python
# Методы
post.is_viral(min_likes=5000)  # Проверка вирусности
post.days_old()                # Возраст в днях
post.is_fresh(max_days=3)      # Проверка свежести
post.to_dict()                 # Сериализация

# Статусы
PostStatus.PARSING
PostStatus.FILTERED
PostStatus.PROCESSING
PostStatus.PROCESSED
PostStatus.APPROVED
PostStatus.REJECTED
PostStatus.POSTED
```

### Модель ProcessedPost

```python
# Методы
processed.get_full_caption()           # Полный caption для Instagram
processed.get_telegram_preview(300)    # Короткий превью
processed.to_dict()                    # Сериализация

# Статусы
ProcessedStatus.PENDING_APPROVAL
ProcessedStatus.APPROVED
ProcessedStatus.REJECTED
ProcessedStatus.POSTED
```

### Модель ApprovalHistory

```python
# Методы
ApprovalHistory.get_latest_for_post(session, post_id)  # Последнее решение
approval.is_approved()                                  # Проверка одобрения
approval.to_dict()                                      # Сериализация

# Решения
DecisionType.APPROVED
DecisionType.REJECTED
DecisionType.EDITED
```

## 🚀 Использование

### 1. Инициализация БД

```bash
python scripts/init_db.py
```

Вывод:
```
🔧 Initializing database...
📍 Database URL: postgresql+asyncpg://user:pass@localhost/dbname
✅ Database initialized successfully!

Created tables:
  - original_posts
  - processed_posts
  - approval_history
```

### 2. Тестирование

```bash
python scripts/test_models.py
```

Проверяет:
- ✅ Создание OriginalPost
- ✅ Создание ProcessedPost
- ✅ Создание ApprovalHistory
- ✅ Связи между моделями
- ✅ Методы моделей
- ✅ Автоматическую очистку

### 3. Проверка в PostgreSQL

```bash
psql -U instagram_bot -d instagram_viral -c "\dt"
```

Должны быть:
```
               List of relations
 Schema |       Name        | Type  |     Owner
--------+-------------------+-------+---------------
 public | approval_history  | table | instagram_bot
 public | original_posts    | table | instagram_bot
 public | processed_posts   | table | instagram_bot
```

## 📋 Checklist

- [x] ✅ app/models/base.py создан (97 строк)
- [x] ✅ app/models/post.py создан (143 строки)
- [x] ✅ app/models/processed_post.py создан (147 строк)
- [x] ✅ app/models/approval.py создан (108 строк)
- [x] ✅ app/models/__init__.py обновлен (23 строки)
- [x] ✅ app/models/README.md создан (документация)
- [x] ✅ scripts/init_db.py создан
- [x] ✅ scripts/test_models.py создан
- [x] ✅ scripts/MIGRATIONS.md создан (руководство)

## 🎨 Особенности реализации

### Async/Await везде
```python
async with get_session() as session:
    result = await session.execute(select(OriginalPost))
    posts = result.scalars().all()
```

### Type hints (Mapped)
```python
id: Mapped[int] = mapped_column(Integer, primary_key=True)
author: Mapped[str] = mapped_column(String(100), nullable=False)
likes: Mapped[int] = mapped_column(Integer, nullable=False)
```

### Enums для статусов
```python
class PostStatus(enum.Enum):
    PARSING = "parsing"
    FILTERED = "filtered"
    # ...
```

### JSON поля
```python
slides: Mapped[List[str]] = mapped_column(JSON, nullable=False)
image_urls: Mapped[List[str]] = mapped_column(JSON, nullable=False)
```

### Автоматические timestamps
```python
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now()
    )
```

### Cascade DELETE
```python
processed_posts: Mapped[List["ProcessedPost"]] = relationship(
    "ProcessedPost",
    back_populates="original_post",
    cascade="all, delete-orphan"
)
```

### Connection pooling
```python
engine = create_async_engine(
    database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

## 📊 Статистика

- **Всего файлов:** 9
- **Строк кода:** 518 (только модели)
- **Моделей:** 3
- **Enums:** 3
- **Таблиц в БД:** 3
- **Индексов:** 10+
- **Методов:** 15+

## 🔄 Следующие шаги

1. **Запустить инициализацию:**
   ```bash
   python scripts/init_db.py
   ```

2. **Протестировать модели:**
   ```bash
   python scripts/test_models.py
   ```

3. **Проверить таблицы в PostgreSQL:**
   ```bash
   psql -U instagram_bot -d instagram_viral -c "\dt"
   ```

4. **Интегрировать с сервисами:**
   - Обновить `app/services/instagram_parser.py` для сохранения в БД
   - Обновить `app/services/ai_rewriter.py` для создания ProcessedPost
   - Обновить `app/handlers/approval.py` для работы с ApprovalHistory

5. **Настроить Alembic миграции:**
   ```bash
   alembic init alembic
   # Настроить env.py и alembic.ini
   ```

## 📚 Документация

- **app/models/README.md** - Полная документация по моделям
- **scripts/MIGRATIONS.md** - Руководство по миграциям
- **PROJECT_STRUCTURE.md** - Общая структура проекта

## 🎉 Готово!

Все SQLAlchemy модели созданы и готовы к использованию!

Следующий шаг: интеграция моделей с существующими сервисами и handlers.
