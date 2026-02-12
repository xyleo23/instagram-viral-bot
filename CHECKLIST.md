# ✅ Instagram Parser - Checklist

## 📋 Что создано

- ✅ **app/services/instagram_parser.py** (348 строк)
  - Асинхронный класс `InstagramParser`
  - Интеграция с ScrapeCreators API
  - Фильтрация вирусных постов
  - Сохранение в БД через SQLAlchemy
  - Полное логирование

- ✅ **scripts/test_parser.py** (60 строк)
  - Тестовый скрипт для проверки парсера
  - Инициализация БД
  - Вывод статистики

- ✅ **PARSER_IMPLEMENTATION.md**
  - Полная документация
  - Примеры использования
  - Troubleshooting guide

## 🔧 Что нужно проверить

### Настройка API

#### ScrapeCreators
1. Зарегистрируйся на https://scrapecreators.com
2. Получи API ключ в личном кабинете
3. Добавь в `.env`: `SCRAPECREATORS_API_KEY=ваш_ключ`
4. 100 бесплатных запросов при регистрации

### 1. Конфигурация .env

```bash
# Проверьте что эти переменные заполнены:
SCRAPECREATORS_API_KEY=your_scrapecreators_api_key
INSTAGRAM_AUTHORS=sanyaagainst,theivansergeev,ivan.loginov_ai
MIN_LIKES=5000
MAX_POST_AGE_DAYS=3
DATABASE_URL=sqlite+aiosqlite:///./instagram_bot.db
```

**Проверка:**
```powershell
Select-String -Path ".env" -Pattern "SCRAPECREATORS_API_KEY"
```

### 2. База данных

Убедитесь, что таблицы созданы:

```bash
python scripts/init_db.py
```

**Ожидаемый вывод:**
```
✅ Database initialized
📊 Tables created: original_posts, processed_posts, approval_history
```

### 3. Зависимости

Все зависимости уже в `requirements.txt`:
- ✅ aiohttp (HTTP клиент)
- ✅ sqlalchemy (ORM)
- ✅ loguru (логирование)
- ✅ asyncpg / aiosqlite (async DB)

## 🚀 Запуск теста

### Шаг 1: Активируйте виртуальное окружение

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Шаг 2: Установите зависимости (если еще не установлены)

```bash
pip install -r requirements.txt
```

### Шаг 3: Запустите тест

```bash
python scripts/test_parser.py
```

### Ожидаемый результат:

```
🔍 Testing Instagram Parser
📋 Authors: ['sanyaagainst', 'theivansergeev', 'ivan.loginov_ai', 'provotorov_pro', 'generalov_ai']
❤️  Min likes: 5000
📅 Max age: 3 days

2026-01-30 10:15:23 | INFO     | Starting Instagram parsing for 2 accounts
2026-01-30 10:15:25 | INFO     | Fetched 12 posts from @sanyaagainst
2026-01-30 10:15:28 | INFO     | Fetched 10 posts from @theivansergeev
2026-01-30 10:15:30 | INFO     | Fetched 47 posts from ScrapeCreators
2026-01-30 10:15:46 | INFO     | Filtered to 8 viral posts

✅ Parsing completed!
📊 Found 8 viral posts

💾 Saved 8 posts to database

============================================================

1. @sanyaagainst (12,450 likes)
   URL: https://www.instagram.com/p/ABC123/
   Text: Как я заработал миллион на AI...
   Posted: 2026-01-29 14:30

2. @theivansergeev (9,800 likes)
   URL: https://www.instagram.com/p/DEF456/
   Text: 5 способов использовать ChatGPT...
   Posted: 2026-01-28 10:15
```

## ❌ Возможные ошибки

### Ошибка 1: "SCRAPECREATORS_API_KEY not set"

**Решение:**
```bash
# Добавьте в .env файл:
SCRAPECREATORS_API_KEY=your_actual_scrapecreators_api_key
```

Получить ключ: https://scrapecreators.com (личный кабинет)

### Ошибка 2: "Table original_posts doesn't exist"

**Решение:**
```bash
python scripts/init_db.py
```

### Ошибка 3: "No module named 'app'"

**Решение:**
```bash
# Убедитесь что вы в корне проекта:
cd c:\Users\Admin\.cursor\instagram_bot

# И запускайте через python -m:
python -m scripts.test_parser
```

### Ошибка 4: "ScrapeCreators API error"

**Возможные причины:**
- Неверный API ключ
- Закончились бесплатные запросы
- Instagram аккаунт приватный

**Решение:**
- Проверьте ключ на https://scrapecreators.com
- Проверьте что аккаунты публичные

### Ошибка 5: "No viral posts found"

**Решение:**
Снизьте пороги в `.env`:
```env
MIN_LIKES=1000
MAX_POST_AGE_DAYS=7
```

## 📊 Проверка результатов

### Проверка в БД (SQLite)

```bash
# Установите sqlite3 (если нет)
# Windows: скачайте с https://sqlite.org/download.html

# Откройте БД
sqlite3 instagram_bot.db

# Проверьте посты
SELECT id, author, likes, status FROM original_posts ORDER BY likes DESC LIMIT 5;

# Выход
.quit
```

### Проверка в коде

```python
import asyncio
from app.models import init_db, get_session, OriginalPost
from app.config import get_config
from sqlalchemy import select

async def check_posts():
    config = get_config()
    init_db(config.get_database_url())
    
    async for session in get_session():
        result = await session.execute(
            select(OriginalPost).order_by(OriginalPost.likes.desc()).limit(5)
        )
        posts = result.scalars().all()
        
        for post in posts:
            print(f"@{post.author}: {post.likes} likes - {post.text[:50]}...")

asyncio.run(check_posts())
```

## 🎯 Следующие шаги

После успешного теста:

1. ✅ Парсер работает
2. ⏳ Интегрировать в Telegram бота (`/parse` команда)
3. ⏳ Добавить в scheduler (автопарсинг каждые 6 часов)
4. ⏳ Добавить retry логику (tenacity)
5. ⏳ Добавить кэширование в Redis
6. ⏳ Настроить мониторинг и алерты

## 📞 Поддержка

Если что-то не работает:

1. Проверьте логи в `logs/bot.log`
2. Проверьте `.env` конфигурацию
3. Проверьте ScrapeCreators API ключ
4. Проверьте что БД инициализирована

## 🎉 Готово!

Если тест прошел успешно - парсер готов к использованию!

---

**Дата:** 2026-01-30  
**Статус:** ✅ Готово к тестированию
