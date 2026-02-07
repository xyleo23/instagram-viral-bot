# ✅ AI Rewriter - Чеклист проверки

## 📋 Перед запуском

- [ ] Установлены зависимости: `aiohttp`, `loguru`
- [ ] Создан `.env` файл из `.env.example`
- [ ] Получен OpenRouter API ключ
- [ ] API ключ добавлен в `.env` как `OPENROUTER_API_KEY`
- [ ] Выбрана модель в `.env` (`OPENROUTER_MODEL`)
- [ ] Пополнен баланс на OpenRouter ($5-10)

## 🧪 Тестирование

### Шаг 1: Базовый тест

```bash
python scripts/test_ai_rewriter.py
```

**Ожидаемый результат:**
- ✅ Подключение к OpenRouter успешно
- ✅ Получен ответ от AI
- ✅ JSON успешно распарсен
- ✅ Создано 8 слайдов
- ✅ Показана стоимость запроса

**Если ошибка:**
- ❌ "OpenRouter API failed" → проверьте API ключ и баланс
- ❌ "Could not parse JSON" → используется fallback (это нормально)
- ❌ "Connection timeout" → проверьте интернет

### Шаг 2: Тест с реальными постами

```bash
# Сначала получите посты
python scripts/test_parser.py

# Затем обработайте их
python scripts/test_ai_rewriter.py
```

**Ожидаемый результат:**
- ✅ Пост загружен из БД
- ✅ AI переписал пост
- ✅ Результат сохранен

### Шаг 3: Примеры использования

```bash
python examples/ai_rewriter_examples.py
```

**Выберите пример:**
1. Базовое использование
2. Батчинг (несколько постов)
3. Сравнение моделей
4. Обработка ошибок
5. Интеграция с БД
6. Кастомный промпт

## 🔍 Проверка функциональности

### ✅ Асинхронность

```python
# Должно работать без блокировки
async def test():
    rewriter = AIRewriter(api_key="...")
    result = await rewriter.rewrite(text="...", author="...")
    await rewriter.close()
```

### ✅ Retry логика

```python
# При ошибке должно быть 3 попытки
# Логи:
# DEBUG: OpenRouter API call attempt 1/3
# WARNING: OpenRouter API error (attempt 1): ...
# DEBUG: OpenRouter API call attempt 2/3
```

### ✅ Fallback парсинг

```python
# При невалидном API ключе должен работать fallback
rewriter = AIRewriter(api_key="invalid")
result = await rewriter.rewrite(...)
assert result["ai_model"] == "fallback"
```

### ✅ Подсчет стоимости

```python
# Должны быть заполнены поля
assert "tokens_used" in result
assert "cost_usd" in result
assert result["cost_usd"] > 0
```

### ✅ Валидация результата

```python
# Должны быть все поля
assert "title" in result
assert "slides" in result
assert "caption" in result
assert "hashtags" in result
assert len(result["slides"]) >= 6
```

## 📊 Проверка качества

### Заголовок (title)

- [ ] Длина 5-10 слов
- [ ] Цепляющий и интересный
- [ ] Вызывает любопытство
- [ ] Обещает ценность

### Слайды (slides)

- [ ] Количество: 8 (или указанное)
- [ ] Длина: 20-30 слов каждый
- [ ] Каждый слайд = одна мысль
- [ ] Логическая последовательность
- [ ] Простой язык, без воды

### Caption

- [ ] Полный текст для Instagram
- [ ] Сохранена главная мысль
- [ ] Добавлены эмоции
- [ ] Есть призыв к действию

### Hashtags

- [ ] 3-5 релевантных хештегов
- [ ] Связаны с темой поста
- [ ] Популярные и нишевые

## 💰 Проверка стоимости

### Claude 3.5 Sonnet

- [ ] Input: ~$0.0024 за 800 токенов
- [ ] Output: ~$0.0060 за 400 токенов
- [ ] Итого: ~$0.003-0.006 за пост

### Gemini Pro 1.5

- [ ] Input: ~$0.001 за 800 токенов
- [ ] Output: ~$0.002 за 400 токенов
- [ ] Итого: ~$0.001-0.003 за пост

### GPT-4 Turbo

- [ ] Input: ~$0.008 за 800 токенов
- [ ] Output: ~$0.012 за 400 токенов
- [ ] Итого: ~$0.010-0.020 за пост

## 🐛 Тестирование ошибок

### Неправильный API ключ

```bash
# В .env установите неправильный ключ
OPENROUTER_API_KEY=invalid_key

# Запустите тест
python scripts/test_ai_rewriter.py
```

**Ожидаемый результат:**
- ⚠️ Используется fallback парсинг
- ✅ Программа не падает
- ✅ Возвращается структурированный результат

### Нет интернета

```bash
# Отключите интернет и запустите
python scripts/test_ai_rewriter.py
```

**Ожидаемый результат:**
- ⚠️ Timeout после 3 попыток
- ✅ Используется fallback
- ✅ Программа не падает

### Пустой текст

```python
result = await rewriter.rewrite(text="", author="@user")
```

**Ожидаемый результат:**
- ✅ Fallback парсинг
- ✅ Возвращается минимальная структура

## 📈 Производительность

### Скорость обработки

- [ ] 1 пост: 5-15 секунд
- [ ] 10 постов (параллельно): 10-20 секунд
- [ ] 100 постов (батчами): 2-5 минут

### Использование памяти

- [ ] < 100 MB для одного запроса
- [ ] < 500 MB для 100 запросов

### Rate limits

- [ ] OpenRouter: ~60 запросов/минуту
- [ ] При превышении: автоматический retry

## 🔒 Безопасность

- [ ] API ключ в `.env`, не в коде
- [ ] `.env` в `.gitignore`
- [ ] Логи не содержат API ключ
- [ ] Ошибки не раскрывают ключ

## 📝 Логирование

### Успешный запрос

```
INFO: Starting AI rewrite for @username post (1234 chars)
DEBUG: OpenRouter API call attempt 1/3
INFO: OpenRouter API success: 1234 tokens
INFO: AI rewrite completed: 8 slides, 1234 tokens, $0.0037
```

### Ошибка с retry

```
INFO: Starting AI rewrite for @username post (1234 chars)
DEBUG: OpenRouter API call attempt 1/3
WARNING: OpenRouter API error (attempt 1): Connection timeout
DEBUG: OpenRouter API call attempt 2/3
INFO: OpenRouter API success: 1234 tokens
```

### Fallback

```
INFO: Starting AI rewrite for @username post (1234 chars)
WARNING: AI response validation failed, using fallback
WARNING: Using fallback parsing
INFO: AI rewrite completed: 8 slides, 0 tokens, $0.0000
```

## ✅ Финальная проверка

После прохождения всех тестов:

- [ ] Базовый тест работает
- [ ] Тест с БД работает
- [ ] Примеры запускаются
- [ ] Fallback работает
- [ ] Стоимость подсчитывается
- [ ] Логи пишутся корректно
- [ ] Ошибки обрабатываются
- [ ] Документация понятна

## 🎉 Готово к продакшену!

Если все пункты отмечены ✅, AI Rewriter готов к использованию в боте.

## 📞 Поддержка

Проблемы? Проверьте:

1. **Документация:** `app/services/README_AI_REWRITER.md`
2. **Быстрый старт:** `QUICK_START_AI_REWRITER.md`
3. **Примеры:** `examples/ai_rewriter_examples.py`
4. **Логи:** `logs/bot.log`

## 🔗 Полезные ссылки

- [OpenRouter Dashboard](https://openrouter.ai/account)
- [OpenRouter Docs](https://openrouter.ai/docs)
- [Claude 3.5 Sonnet](https://www.anthropic.com/claude)
- [Pricing Calculator](https://openrouter.ai/models)
