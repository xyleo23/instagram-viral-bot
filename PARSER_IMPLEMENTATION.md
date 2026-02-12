# ✅ Instagram Parser Implementation Complete

## 📦 Созданные файлы

### 1. `app/services/instagram_parser.py` (~420 строк)

Полнофункциональный асинхронный парсер Instagram через ScrapeCreators API.

**Основные возможности:**

- ✅ Асинхронный класс `InstagramParser`
- ✅ Интеграция с ScrapeCreators API
- ✅ Прямой запрос к API (без ожидания задач)
- ✅ Фильтрация вирусных постов по критериям:
  - Минимальное количество лайков
  - Максимальный возраст поста
  - Минимальная длина текста
- ✅ Сохранение в БД через SQLAlchemy (async)
- ✅ Логирование всех операций через loguru
- ✅ Обработка дубликатов
- ✅ Graceful error handling

**Ключевые методы:**

```python
# Парсинг аккаунтов
posts = await parser.parse_accounts(
    accounts=["username1", "username2"],
    min_likes=5000,
    max_age_days=3,
    posts_limit=10
)

# Фильтрация вирусных постов
filtered = parser.filter_viral_posts(
    posts,
    min_likes=5000,
    max_age_days=3,
    min_text_length=100
)

# Сохранение в БД
saved = await parser.save_to_db(posts, status=PostStatus.FILTERED)
```

### 2. `scripts/test_parser.py` (~80 строк)

Тестовый скрипт для проверки работы парсера.

**Что делает:**

- Инициализирует БД и логирование
- Парсит первых 2 авторов из конфига
- Фильтрует вирусные посты
- Сохраняет в базу данных
- Выводит красивую статистику

## 🚀 Как использовать

### 1. Проверьте конфигурацию

Убедитесь, что в `.env` файле заполнены:

```env
# ScrapeCreators API
SCRAPECREATORS_API_KEY=your_scrapecreators_api_key

# Instagram авторы
INSTAGRAM_AUTHORS=sanyaagainst,theivansergeev,ivan.loginov_ai

# Фильтры
MIN_LIKES=5000
MAX_POST_AGE_DAYS=3
MIN_TEXT_LENGTH=100
```

### 2. Получите ScrapeCreators API ключ

1. Зарегистрируйтесь на https://scrapecreators.com
2. Получите API ключ в личном кабинете
3. Добавьте в `.env` файл
4. 100 бесплатных запросов при регистрации

### 3. Запустите тест

```bash
python scripts/test_parser.py
```

**Ожидаемый вывод:**

```
🔍 Testing Instagram Parser
📋 Authors: ['sanyaagainst', 'theivansergeev', ...]
❤️  Min likes: 5000
📅 Max age: 3 days

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

## 🔄 Интеграция в основной бот

### В handler'е `/parse`

```python
from app.services.instagram_parser import InstagramParser
from app.config import get_config

@router.message(Command("parse"))
async def cmd_parse(message: Message):
    config = get_config()
    parser = InstagramParser(settings=config)

    try:
        await message.answer("🔍 Начинаю парсинг Instagram...")

        posts = await parser.parse_accounts(
            accounts=config.instagram_authors_list,
            min_likes=config.MIN_LIKES,
            max_age_days=config.MAX_POST_AGE_DAYS,
            posts_limit=10
        )

        saved = await parser.save_to_db(posts)

        await message.answer(
            f"✅ Парсинг завершен!\n"
            f"📊 Найдено {len(posts)} вирусных постов\n"
            f"💾 Сохранено {len(saved)} новых постов"
        )
    finally:
        pass
```

### В scheduler'е (автоматический парсинг)

```python
from app.services.instagram_parser import InstagramParser
from app.config import get_config

async def scheduled_parse():
    """Автоматический парсинг каждые 6 часов."""
    config = get_config()
    parser = InstagramParser(settings=config)

    try:
        posts = await parser.parse_accounts(
            accounts=config.instagram_authors_list,
            min_likes=config.MIN_LIKES,
            max_age_days=config.MAX_POST_AGE_DAYS,
            posts_limit=10
        )

        saved = await parser.save_to_db(posts)
        logger.info(f"Scheduled parse: {len(saved)} new posts saved")
    finally:
        pass
```

## 📊 ScrapeCreators API

**Base URL:** `https://api.scrapecreators.com/v1`

**Endpoint:** `GET /instagram/profile?handle=username`

**Auth:** Header `x-api-key: YOUR_API_KEY`

**Ответ:** JSON с постами в `data.edge_felix_video_timeline.edges` или `data.edge_owner_to_timeline_media.edges`

```json
{
  "success": true,
  "data": {
    "edge_felix_video_timeline": {
      "edges": [
        {
          "node": {
            "shortcode": "ABC123",
            "edge_media_to_caption": {"edges": [{"node": {"text": "..."}}]},
            "edge_liked_by": {"count": 12450},
            "edge_media_to_comment": {"count": 234},
            "taken_at_timestamp": 1706538600,
            "is_video": true,
            "display_url": "...",
            "video_url": "..."
          }
        }
      ]
    }
  }
}
```

Парсер автоматически конвертирует это в модель `OriginalPost`:

```python
OriginalPost(
    external_id="ABC123",
    author="sanyaagainst",
    author_url="https://www.instagram.com/sanyaagainst/",
    text="Полный текст поста...",
    likes=12450,
    comments=234,
    engagement=0.0,
    post_url="https://www.instagram.com/p/ABC123/",
    posted_at=datetime(2026, 1, 29, 14, 30),
    status=PostStatus.FILTERED
)
```

## ⚙️ Конфигурация

Все настройки парсера управляются через `app/config.py`:

```python
# ScrapeCreators
SCRAPECREATORS_API_KEY: str  # API ключ

# Instagram
INSTAGRAM_AUTHORS: str  # Список авторов через запятую
MIN_LIKES: int = 5000  # Минимум лайков
MAX_POST_AGE_DAYS: int = 3  # Максимальный возраст
MIN_TEXT_LENGTH: int = 100  # Минимальная длина текста
```

## 🔍 Логирование

Парсер логирует все операции:

```
2026-01-30 10:15:23 | INFO     | Starting Instagram parsing for 5 accounts
2026-01-30 10:15:25 | INFO     | Fetched 12 posts from @sanyaagainst
2026-01-30 10:15:28 | INFO     | Fetched 10 posts from @theivansergeev
2026-01-30 10:15:30 | INFO     | Fetched 47 posts from ScrapeCreators
2026-01-30 10:15:30 | INFO     | Filtered to 8 viral posts
2026-01-30 10:15:31 | INFO     | Saved post ABC123 from @sanyaagainst
2026-01-30 10:15:31 | INFO     | Saved 8 new posts to database
```

## 🛡️ Error Handling

Парсер обрабатывает все типы ошибок:

1. **HTTP ошибки** - если ScrapeCreators API недоступен
2. **Дубликаты** - если пост уже есть в БД (по `external_id`)
3. **Некорректные данные** - если пост не содержит обязательных полей
4. **Database ошибки** - откат транзакции при ошибке сохранения

## 📈 Производительность

- **Скорость парсинга**: ~1-3 секунды на аккаунт (прямой API запрос)
- **Лимиты ScrapeCreators**: 100 бесплатных запросов при регистрации
- **Рекомендуемая частота**: каждые 6 часов (4 раза в день)

## 🔄 Следующие шаги

1. ✅ Парсер создан
2. ✅ Тестовый скрипт создан
3. ⏳ Интегрировать в `/parse` handler
4. ⏳ Добавить в scheduler для автоматического парсинга
5. ⏳ Добавить retry логику (tenacity)
6. ⏳ Добавить кэширование в Redis
7. ⏳ Добавить метрики и мониторинг

## 🐛 Troubleshooting

### Ошибка: "SCRAPECREATORS_API_KEY not found"

Убедитесь, что в `.env` файле есть:

```env
SCRAPECREATORS_API_KEY=your_actual_api_key_here
```

### Ошибка: "API error" (success: false)

Возможные причины:
- Неверный API ключ
- Закончились бесплатные запросы
- Аккаунт Instagram приватный или заблокирован

### Ошибка: "No viral posts found"

Возможные причины:
- Слишком высокий `MIN_LIKES` порог
- Слишком короткий `MAX_POST_AGE_DAYS`
- У авторов нет свежих вирусных постов

Попробуйте снизить пороги:

```env
MIN_LIKES=1000
MAX_POST_AGE_DAYS=7
```

## 📚 Полезные ссылки

- [ScrapeCreators](https://scrapecreators.com)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Loguru Documentation](https://loguru.readthedocs.io/)

---

**Статус:** ✅ Готово к использованию

**Дата создания:** 2026-01-30

**Версия:** 2.0.0 (ScrapeCreators)
