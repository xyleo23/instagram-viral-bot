# API и токены для настройки Instagram Viral Bot

## Обязательные (без них приложение не запустится)

| Переменная | Назначение | Где взять |
|------------|------------|-----------|
| **BOT_TOKEN** | Telegram Bot API | [@BotFather](https://t.me/BotFather) → `/newbot` → скопировать токен |
| **ADMIN_CHAT_ID** | ID твоего Telegram (доступ только у тебя) | Узнать: написать боту [@userinfobot](https://t.me/userinfobot) или [@getmyid_bot](https://t.me/getmyid_bot) → число в поле "Id" |
| **OPENROUTER_API_KEY** | AI переписывание текстов (Claude 3.5) | [OpenRouter.ai](https://openrouter.ai) → Sign up → API Keys → Create Key |
| **ORSHOT_API_KEY** | Генерация слайдов карусели (изображения) | [Orshot](https://orshot.com) — зарегистрироваться и получить API ключ |

В `.env` также указывается **ORSOT_TEMPLATE_ID** (по умолчанию `2685`) — ID шаблона в Orshot для слайдов.

---

## Нужны для полного цикла (парсинг → одобрение → выгрузка)

| Переменная | Назначение | Где взять |
|------------|------------|-----------|
| **APIFY_API_KEY** | Парсинг Instagram (посты, лайки, авторы) | [Apify](https://apify.com) → Sign up → Settings → Integrations → API Token. В проекте используется актор `apify/instagram-scraper`. |

Без **APIFY_API_KEY** команда `/parse` и фоновый парсинг по расписанию не будут работать.

---

## Опциональные (можно оставить пустыми)

| Переменная | Назначение | Где взять |
|------------|------------|-----------|
| **YANDEX_DISK_TOKEN** | Загрузка готовых каруселей на Яндекс.Диск | [Яндекс OAuth](https://oauth.yandex.ru) — приложение с доступом к Диску, получить OAuth-токен. Без токена шаг «загрузка на Диск» в обработке поста будет падать (остальной пайплайн — парсинг, AI, карусель — работает). |
| **GOOGLE_SHEETS_ID** | (TODO) Экспорт в Google Таблицы | — |
| **GOOGLE_DRIVE_FOLDER_ID** | (TODO) Выгрузка в Google Drive | — |
| **GOOGLE_CREDENTIALS_FILE** | (TODO) Файл `credentials.json` для Google API | — |

---

## Где что используется в коде

- **BOT_TOKEN** — запуск бота (`app.bot.main`), отправка уведомлений из Celery.
- **ADMIN_CHAT_ID** — проверка в хендлерах (`start.py`, `queue.py`, `approval.py`, `history.py`): ответ только тебе.
- **OPENROUTER_API_KEY** — `app.services.ai_rewriter`, задача `app.workers.tasks.processing` (переписывание текста).
- **ORSHOT_API_KEY** — `app.services.carousel_generator`, задача processing (генерация картинок карусели).
- **APIFY_API_KEY** — `app.services.instagram_parser`, задача `app.workers.tasks.parsing` и команда `/parse`.
- **YANDEX_DISK_TOKEN** — `app.services.yandex_disk`, задача processing (загрузка изображений на Диск).

---

## Минимальный рабочий `.env`

Чтобы только запустить бота и меню (без парсинга и обработки постов):

```env
BOT_TOKEN=123456:ABC...
ADMIN_CHAT_ID=123456789
OPENROUTER_API_KEY=sk-or-...
ORSHOT_API_KEY=ваш_ключ_orshot
APIFY_API_KEY=
YANDEX_DISK_TOKEN=
```

Для полного цикла (парсинг → AI → карусель → Диск → одобрение) заполни также **APIFY_API_KEY** и **YANDEX_DISK_TOKEN**.
