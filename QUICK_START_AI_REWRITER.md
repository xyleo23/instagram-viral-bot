# 🚀 Быстрый старт AI Rewriter

## 1️⃣ Получите OpenRouter API ключ

1. Перейдите на [openrouter.ai](https://openrouter.ai/)
2. Зарегистрируйтесь (можно через Google/GitHub)
3. Пополните баланс: **Settings → Credits → Add Credits** ($5 хватит надолго)
4. Создайте API ключ: **Keys → Create Key**
5. Скопируйте ключ (начинается с `sk-or-v1-...`)

## 2️⃣ Настройте .env

Откройте `.env` и добавьте:

```env
OPENROUTER_API_KEY=sk-or-v1-ваш-ключ-здесь
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

## 3️⃣ Запустите тест

```bash
python scripts/test_ai_rewriter.py
```

## ✅ Ожидаемый результат

```
🤖 Testing AI Rewriter

Model: anthropic/claude-3.5-sonnet
Temperature: 0.85

⏳ Rewriting with AI...

✅ AI Rewrite completed!

======================================================================

📝 NEW TITLE:
7 ошибок которые убивают ваш бизнес

📊 SLIDES (8):

1. Успех это не про идеи
2. Это про исполнение
3. У меня было 10 провалов
4. И только одна идея выстрелила
5. Но она изменила всё
6. Доход 500к+ в месяц
7. Начните делать сейчас
8. Идеальный момент никогда не наступит

💬 CAPTION:
Сегодня я хочу поделиться с вами своим опытом...

🏷️  HASHTAGS:
#бизнес #успех #мотивация #предприниматель #ai

======================================================================

💰 Cost: $0.0037
🔢 Tokens: 1234
🤖 Model: anthropic/claude-3.5-sonnet
```

## 💰 Стоимость

- **1 пост** ≈ $0.003-0.006
- **100 постов** ≈ $0.30-0.60
- **1000 постов** ≈ $3-6

## 🎯 Доступные модели

Измените `OPENROUTER_MODEL` в `.env`:

```env
# Рекомендуется (лучшее качество/цена)
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Самая дешевая
OPENROUTER_MODEL=google/gemini-pro-1.5

# Максимальное качество
OPENROUTER_MODEL=openai/gpt-4-turbo
```

## 🐛 Проблемы?

### "OpenRouter API failed"

✅ Проверьте API ключ в `.env`  
✅ Проверьте баланс на [openrouter.ai/account](https://openrouter.ai/account)  
✅ Проверьте интернет соединение  

### "No posts found in database"

✅ Сначала запустите парсер: `python scripts/test_parser.py`  
✅ Или используйте fallback тестовый пост (автоматически)  

### Медленная работа

✅ Нормально, AI обработка занимает 5-15 секунд  
✅ Используйте Gemini для ускорения  

## 📚 Дополнительно

- Полная документация: `app/services/README_AI_REWRITER.md`
- Примеры использования: `app/services/ai_rewriter.py` (внизу файла)
- Настройка промпта: отредактируйте `_build_prompt()` в `ai_rewriter.py`

## 🎉 Готово!

Теперь вы можете использовать AI Rewriter в своем боте:

```python
from app.services.ai_rewriter import AIRewriter
from app.config import get_config

config = get_config()
rewriter = AIRewriter(
    api_key=config.OPENROUTER_API_KEY,
    model=config.OPENROUTER_MODEL
)

result = await rewriter.rewrite(
    text="Ваш пост",
    author="@username"
)
```
