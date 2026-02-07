# Database Migrations Guide

Руководство по работе с миграциями базы данных через Alembic.

## 🚀 Быстрый старт

### 1. Инициализация БД (первый запуск)

```bash
# Создать все таблицы с нуля
python scripts/init_db.py
```

### 2. Тестирование моделей

```bash
# Запустить тестовый скрипт
python scripts/test_models.py
```

## 📋 Alembic Setup (TODO)

### Инициализация Alembic

```bash
# Инициализировать Alembic (выполнить один раз)
cd instagram_bot
alembic init alembic
```

### Настройка alembic.ini

Отредактировать `alembic.ini`:

```ini
# Закомментировать статическую строку
# sqlalchemy.url = driver://user:pass@localhost/dbname

# Использовать динамическую загрузку из .env
```

### Настройка env.py

Отредактировать `alembic/env.py`:

```python
from app.config import get_config
from app.models import Base

# Загрузка конфигурации
config_obj = get_config()
config.set_main_option("sqlalchemy.url", config_obj.get_database_url(sync=True))

# Метаданные для автогенерации
target_metadata = Base.metadata
```

## 🔄 Работа с миграциями

### Создание миграции

```bash
# Автогенерация миграции на основе изменений моделей
alembic revision --autogenerate -m "Add new field to posts"

# Ручное создание пустой миграции
alembic revision -m "Custom migration"
```

### Применение миграций

```bash
# Применить все миграции
alembic upgrade head

# Применить конкретную миграцию
alembic upgrade <revision_id>

# Откатить одну миграцию
alembic downgrade -1

# Откатить все миграции
alembic downgrade base
```

### Просмотр истории

```bash
# Показать текущую версию
alembic current

# Показать историю миграций
alembic history

# Показать SQL без применения
alembic upgrade head --sql
```

## 📝 Примеры миграций

### Добавление нового поля

```python
# alembic/versions/xxx_add_views_count.py
def upgrade():
    op.add_column('original_posts', sa.Column('views', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('original_posts', 'views')
```

### Изменение типа поля

```python
def upgrade():
    op.alter_column('original_posts', 'likes',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)

def downgrade():
    op.alter_column('original_posts', 'likes',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False)
```

### Добавление индекса

```python
def upgrade():
    op.create_index('idx_posts_author_status', 'original_posts', ['author', 'status'])

def downgrade():
    op.drop_index('idx_posts_author_status', table_name='original_posts')
```

## 🛠️ Полезные команды

### Проверка состояния БД

```bash
# PostgreSQL
psql -U instagram_bot -d instagram_viral -c "\dt"
psql -U instagram_bot -d instagram_viral -c "\d original_posts"

# Подсчет записей
psql -U instagram_bot -d instagram_viral -c "SELECT COUNT(*) FROM original_posts;"
```

### Сброс БД (осторожно!)

```bash
# Удалить все таблицы
python -c "import asyncio; from app.models import init_db, drop_tables; from app.config import get_config; config = get_config(); init_db(config.get_database_url()); asyncio.run(drop_tables())"

# Создать заново
python scripts/init_db.py
```

## 📊 Структура таблиц

### original_posts

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| external_id | String(100) | Instagram post ID (unique) |
| author | String(100) | Instagram username |
| author_url | String(255) | Profile URL |
| text | Text | Post text |
| likes | Integer | Likes count |
| comments | Integer | Comments count |
| engagement | Float | Engagement rate |
| post_url | String(500) | Direct link |
| posted_at | DateTime | Instagram post date |
| status | Enum | Post status |
| created_at | DateTime | Created timestamp |
| updated_at | DateTime | Updated timestamp |

### processed_posts

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| original_post_id | Integer | FK to original_posts |
| title | String(200) | New title |
| caption | Text | Rewritten caption |
| hashtags | String(500) | Hashtags |
| slides | JSON | Slide texts array |
| slides_count | Integer | Number of slides |
| ai_model | String(100) | AI model used |
| tokens_used | Integer | Tokens consumed |
| cost_usd | Float | Processing cost |
| image_urls | JSON | Image URLs array |
| yandex_disk_folder | String(500) | Yandex.Disk path |
| status | Enum | Processing status |
| created_at | DateTime | Created timestamp |
| updated_at | DateTime | Updated timestamp |

### approval_history

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| processed_post_id | Integer | FK to processed_posts |
| user_id | Integer | Telegram User ID |
| username | String(100) | Telegram username |
| decision | Enum | Approval decision |
| comment | Text | Admin comment |
| timestamp | DateTime | Decision time |

## 🔗 Связи

```
original_posts (1) ──< (N) processed_posts (1) ──< (N) approval_history
```

- CASCADE DELETE: При удалении original_post удаляются все связанные processed_posts
- CASCADE DELETE: При удалении processed_post удаляются все связанные approval_history

## 🎯 Best Practices

1. **Всегда создавайте миграции** для изменений схемы БД
2. **Тестируйте миграции** на dev окружении перед production
3. **Делайте backup** перед применением миграций на production
4. **Используйте транзакции** для критичных операций
5. **Добавляйте индексы** для часто используемых запросов
6. **Не удаляйте старые миграции** из истории

## 📚 Дополнительно

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
