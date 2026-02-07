# 🤖 AI Rewriter Service

Сервис для переписывания постов Instagram в виральный формат через OpenRouter API.

## 📋 Возможности

✅ **Асинхронная работа** - полностью async/await  
✅ **Поддержка топовых моделей** - Claude 3.5 Sonnet, GPT-4 Turbo, Gemini Pro 1.5  
✅ **Умный промпт** - генерация каруселей в стиле @theivansergeev  
✅ **Парсинг JSON** - с fallback если AI вернул невалидный формат  
✅ **Подсчет токенов и стоимости** - отслеживание расходов  
✅ **Retry логика** - автоматические повторы при ошибках  
✅ **Полное логирование** - все запросы логируются через loguru  

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install aiohttp loguru
```

### 2. Настройка .env

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

### 3. Получение API ключа

1. Зарегистрируйтесь на [OpenRouter](https://openrouter.ai/)
2. Пополните баланс ($5-10 хватит надолго)
3. Создайте API ключ в разделе Keys
4. Добавьте в `.env`

### 4. Запуск теста

```bash
python scripts/test_ai_rewriter.py
```

## 💻 Использование

### Базовое использование

```python
from app.services.ai_rewriter import AIRewriter
from app.config import get_config

config = get_config()

rewriter = AIRewriter(
    api_key=config.OPENROUTER_API_KEY,
    model=config.OPENROUTER_MODEL,
    temperature=0.85
)

try:
    result = await rewriter.rewrite(
        text="Ваш оригинальный пост...",
        author="@username",
        slides_count=8
    )
    
    print(f"Title: {result['title']}")
    print(f"Slides: {len(result['slides'])}")
    print(f"Cost: ${result['cost_usd']:.4f}")
    
finally:
    await rewriter.close()
```

### Формат ответа

```python
{
    "title": "Цепляющий заголовок",
    "slides": [
        "Слайд 1 текст",
        "Слайд 2 текст",
        # ... 8 слайдов
    ],
    "caption": "Полный текст для Instagram",
    "hashtags": "#тег1 #тег2 #тег3",
    "tokens_used": 1234,
    "cost_usd": 0.0037,
    "ai_model": "anthropic/claude-3.5-sonnet"
}
```

## 🎯 Доступные модели

| Модель | Input ($/1M) | Output ($/1M) | Качество | Скорость |
|--------|--------------|---------------|----------|----------|
| **Claude 3.5 Sonnet** | $3.00 | $15.00 | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ |
| GPT-4 Turbo | $10.00 | $30.00 | ⭐⭐⭐⭐⭐ | ⚡⚡ |
| Gemini Pro 1.5 | $1.25 | $5.00 | ⭐⭐⭐⭐ | ⚡⚡⚡⚡ |

**Рекомендация:** Claude 3.5 Sonnet - лучшее соотношение цена/качество.

## 💰 Стоимость

Средний запрос:
- **Входные токены:** ~800
- **Выходные токены:** ~400
- **Стоимость:** ~$0.003-0.006 за пост

**100 постов ≈ $0.30-0.60**

## 🔧 Параметры

### AIRewriter.__init__()

```python
AIRewriter(
    api_key: str,              # OpenRouter API ключ
    model: str,                # Модель AI
    temperature: float = 0.85  # Креативность (0-1)
)
```

### rewrite()

```python
await rewriter.rewrite(
    text: str,              # Оригинальный текст
    author: str,            # @username автора
    slides_count: int = 8,  # Количество слайдов
    style: str = "viral"    # Стиль (viral/minimalist/educational)
)
```

## 🛡️ Обработка ошибок

### Retry логика

Автоматически повторяет запрос до 3 раз с exponential backoff:
- 1 попытка: сразу
- 2 попытка: через 2 сек
- 3 попытка: через 4 сек

### Fallback парсинг

Если AI не вернул валидный JSON, используется простой парсер:
- Разбивает текст на предложения
- Группирует в слайды
- Возвращает базовую структуру

```python
{
    "title": "Первое предложение",
    "slides": [...],
    "caption": "Оригинальный текст",
    "hashtags": "#мотивация #успех",
    "tokens_used": 0,
    "cost_usd": 0.0,
    "ai_model": "fallback"
}
```

## 📊 Логирование

Все запросы логируются:

```
INFO: Starting AI rewrite for @username post (1234 chars)
DEBUG: OpenRouter API call attempt 1/3
INFO: OpenRouter API success: 1234 tokens
INFO: AI rewrite completed: 8 slides, 1234 tokens, $0.0037
```

При ошибках:

```
WARNING: AI response validation failed, using fallback
ERROR: Error in AI rewrite: Could not parse JSON
```

## 🧪 Тестирование

### Тест с реальным постом из БД

```bash
python scripts/test_ai_rewriter.py
```

### Тест с кастомным текстом

```python
from app.services.ai_rewriter import AIRewriter

rewriter = AIRewriter(api_key="sk-or-v1-xxx")

result = await rewriter.rewrite(
    text="Ваш тестовый пост",
    author="@test"
)

print(result)
```

## 🎨 Промпт инженеринг

Промпт оптимизирован для:

1. **Структура** - четкое разбиение на слайды
2. **Стиль** - минимализм как у топовых блогеров
3. **Вовлечение** - эмоциональные триггеры
4. **Конкретика** - примеры и факты
5. **CTA** - призыв к действию

### Кастомизация промпта

Отредактируйте метод `_build_prompt()` в `ai_rewriter.py`:

```python
def _build_prompt(self, text, author, slides_count, style):
    # Ваш кастомный промпт
    return f"Переписать пост: {text}"
```

## 🔍 Валидация результата

Проверяется:
- ✅ Наличие всех ключей (title, slides, caption, hashtags)
- ✅ slides это list
- ✅ Количество слайдов >= expected - 2
- ✅ Каждый слайд >= 10 символов

Если валидация не прошла → fallback парсинг.

## 📈 Оптимизация стоимости

### 1. Используйте кеширование

```python
# Сохраняйте результаты в БД
if cached_result := get_from_cache(post_id):
    return cached_result
```

### 2. Батчинг

```python
# Обрабатывайте несколько постов за раз
tasks = [rewriter.rewrite(post.text, post.author) for post in posts]
results = await asyncio.gather(*tasks)
```

### 3. Выбор модели

- **Gemini Pro 1.5** - самая дешевая ($1.25/1M input)
- **Claude 3.5** - лучшее качество за разумную цену
- **GPT-4** - только для критичных задач

## ⚠️ Важные замечания

1. **API ключ** - храните в `.env`, не коммитьте в git
2. **Rate limits** - OpenRouter имеет лимиты запросов
3. **Timeout** - по умолчанию 120 сек, можно изменить
4. **Session** - всегда закрывайте через `await rewriter.close()`
5. **Fallback** - всегда работает даже без API ключа

## 🐛 Troubleshooting

### Ошибка: "OpenRouter API failed"

```bash
# Проверьте API ключ
echo $OPENROUTER_API_KEY

# Проверьте баланс на OpenRouter
# https://openrouter.ai/account
```

### Ошибка: "Could not parse JSON"

AI вернул невалидный JSON → автоматически используется fallback.

### Медленная работа

- Уменьшите `max_tokens` в `_call_openrouter()`
- Используйте более быструю модель (Gemini)
- Проверьте интернет соединение

## 📚 Дополнительно

- [OpenRouter Docs](https://openrouter.ai/docs)
- [Claude 3.5 Sonnet](https://www.anthropic.com/claude)
- [GPT-4 Turbo](https://platform.openai.com/docs/models/gpt-4-turbo-and-gpt-4)
- [Gemini Pro](https://ai.google.dev/gemini-api/docs)

## 🤝 Поддержка

Вопросы? Проблемы? Создайте issue в репозитории.
