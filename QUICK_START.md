# 🚀 Быстрый старт

## Шаг 1: Установка зависимостей

```bash
# Создайте виртуальное окружение
python -m venv venv

# Активируйте его
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

## Шаг 2: Настройка конфигурации

1. Скопируйте `.env.example` в `.env`:
```bash
cp .env.example .env
```

2. Заполните необходимые ключи в `.env`:
```env
BOT_TOKEN=ваш_токен_от_BotFather
OPENROUTER_API_KEY=ваш_ключ_openrouter
ORSOT_API_KEY=ваш_ключ_orshot
```

## Шаг 3: Получение API ключей

### Telegram Bot Token
1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `.env`

### OpenRouter API Key
1. Зарегистрируйтесь на [OpenRouter.ai](https://openrouter.ai)
2. Создайте API ключ
3. Скопируйте в `.env`

### Orshot API Key
1. Зарегистрируйтесь на [Orshot.com](https://orshot.com)
2. Получите API ключ
3. Скопируйте в `.env`

## Шаг 4: Инициализация базы данных

```bash
python scripts/init_db.py
```

## Шаг 5: Запуск бота

**Рекомендуемый способ (Docker)** — всё поднимается одной командой:

```bash
cd instagram_bot
docker compose up -d --build
docker compose logs -f bot
```

**Локальный запуск** — нужны Python 3.11 или 3.12 (не 3.14), Redis и установленные зависимости:

```bash
# Точка входа — бот (app.bot.main)
python -m app.bot.main
```

Для работы бота локально нужен запущенный **Redis** (иначе FSM не работает). При использовании Docker Redis поднимается автоматически.

## Шаг 6: Проверка работы

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Отправьте `/parse` для тестового парсинга

## ✅ Готово!

Бот должен запуститься и быть готовым к работе.

## 🔧 Следующие шаги

1. **Настройте список авторов** в `app/services/instagram_parser.py`
2. **Добавьте базу данных** для хранения постов
3. **Настройте расписание** в `app/services/scheduler.py`
4. **Добавьте интеграцию с Google Sheets** (опционально)

## ❓ Проблемы?

- Проверьте, что все API ключи заполнены в `.env`
- Убедитесь, что виртуальное окружение активировано
- Проверьте логи в `logs/bot.log`
