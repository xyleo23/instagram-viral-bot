# 📋 Система одобрения постов

## Описание

Полная система одобрения постов с отправкой превью изображений в Telegram.

## Возможности

✅ **Отправка медиа-группы** - до 10 изображений в карусели  
✅ **Красивое форматирование** - структурированный текст с эмодзи  
✅ **Интерактивные кнопки** - одобрить, отклонить, редактировать  
✅ **FSM для редактирования** - изменение текста и хештегов  
✅ **Интеграция с Celery** - автоматическая отправка после обработки  
✅ **История одобрений** - сохранение всех действий в БД

## Архитектура

### 1. Основная функция: `send_post_for_approval()`

```python
async def send_post_for_approval(
    bot: Bot,
    processed_post_id: int
) -> None:
    """
    Отправляет пост на одобрение админу.
    
    Шаги:
    1. Загрузка поста из БД
    2. Подготовка медиа-группы
    3. Отправка изображений
    4. Формирование текста
    5. Отправка текста с кнопками
    """
```

### 2. Подготовка изображений: `_prepare_media_group()`

Поддерживаемые форматы:
- **Base64**: `data:image/png;base64,...`
- **URL**: `http://...` или `https://...`
- **Яндекс.Диск**: публичные ссылки

Ограничения:
- Максимум 10 изображений (лимит Telegram)
- Автоматическое преобразование base64 в `BufferedInputFile`

### 3. Форматирование текста: `_format_approval_message()`

Структура сообщения:
```
📊 НОВЫЙ ПОСТ НА ПРОВЕРКУ

Источник:
- Author, likes, comments
- Ссылка на оригинал

━━━━━━━━━━━━━━━━━━━━

Новый контент:
- Заголовок
- Текст
- Хештеги

━━━━━━━━━━━━━━━━━━━━

Метрики:
- AI модель
- Токены и стоимость
- Количество слайдов
```

## Callback Handlers

### 1. Одобрение (`approve:`)

```python
@router.callback_query(F.data.startswith("approve:"))
async def callback_approve(callback: CallbackQuery, state: FSMContext):
    """
    Действия:
    1. Обновить статус -> APPROVED
    2. Сохранить в ApprovalHistory
    3. Отправить подтверждение
    """
```

### 2. Отклонение (`reject:`)

```python
@router.callback_query(F.data.startswith("reject:"))
async def callback_reject(callback: CallbackQuery, state: FSMContext):
    """
    Действия:
    1. Обновить статус -> REJECTED
    2. Сохранить в ApprovalHistory
    3. Отправить подтверждение
    """
```

### 3. Редактирование текста (`edit_caption:`)

```python
@router.callback_query(F.data.startswith("edit_caption:"))
async def callback_edit_caption(callback: CallbackQuery, state: FSMContext):
    """
    FSM States:
    1. Установить состояние editing_caption
    2. Ожидать новый текст
    3. Сохранить и обновить
    """
```

### 4. Редактирование хештегов (`edit_hashtags:`)

```python
@router.callback_query(F.data.startswith("edit_hashtags:"))
async def callback_edit_hashtags(callback: CallbackQuery, state: FSMContext):
    """
    FSM States:
    1. Установить состояние editing_hashtags
    2. Ожидать новые хештеги
    3. Сохранить и обновить
    """
```

## FSM States

Определены в `app/bot/states.py`:

```python
class ApprovalStates(StatesGroup):
    waiting_approval = State()
    editing_caption = State()
    editing_hashtags = State()
```

## Интеграция с Celery Worker

В `app/workers/tasks/processing.py`:

```python
# После создания ProcessedPost
from aiogram import Bot
from app.bot.handlers.approval import send_post_for_approval

bot = Bot(token=config.BOT_TOKEN)
try:
    await send_post_for_approval(bot, processed_post.id)
    logger.info(f"Approval notification sent")
except Exception as e:
    logger.error(f"Error sending notification: {e}")
finally:
    await bot.session.close()
```

## Использование

### 1. Запуск бота

```bash
python -m app.bot.main
```

### 2. Запуск worker

```bash
celery -A app.workers.celery_app worker -l INFO
```

### 3. Тестирование

```bash
# Тест отправки уведомления
python scripts/test_approval_notification.py

# Полный тест обработки поста
python scripts/test_celery_worker.py
```

## Проверка работы

### 1. В Telegram должно прийти:

1. **Медиа-группа** - карусель изображений (до 10 шт)
2. **Текстовое сообщение** с:
   - Информацией об источнике
   - Новым контентом
   - Метриками обработки
3. **Интерактивные кнопки**:
   - ✅ Одобрить
   - ❌ Отклонить
   - ✏️ Редактировать текст
   - 🏷 Изменить хештеги
   - 🔗 Открыть на Яндекс.Диске

### 2. Проверка кнопок:

#### ✅ Одобрить
- Статус меняется на `APPROVED`
- Запись в `ApprovalHistory`
- Сообщение обновляется с подтверждением

#### ❌ Отклонить
- Статус меняется на `REJECTED`
- Запись в `ApprovalHistory`
- Сообщение обновляется

#### ✏️ Редактировать текст
- Запускается FSM состояние `editing_caption`
- Бот ожидает новый текст
- Текст обновляется в БД
- Для отмены: `/cancel`

#### 🏷 Изменить хештеги
- Запускается FSM состояние `editing_hashtags`
- Бот ожидает новые хештеги
- Хештеги обновляются в БД
- Для отмены: `/cancel`

## База данных

### ApprovalHistory

```python
class ApprovalHistory(Base):
    id: int
    processed_post_id: int
    user_id: int
    username: str
    decision: DecisionType  # APPROVED / REJECTED
    comment: Optional[str]
    timestamp: datetime
```

### ProcessedPost статусы

```python
class ProcessedStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
```

## Логирование

Все действия логируются с помощью `loguru`:

```python
logger.info(f"Sending ProcessedPost {post_id} for approval")
logger.info(f"Prepared {len(media_group)} images")
logger.info(f"Post {post_id} approved by {user_id}")
logger.error(f"Error sending post for approval: {e}")
```

## Обработка ошибок

### 1. Пост не найден
```python
if not processed_post:
    logger.error(f"ProcessedPost {post_id} not found")
    return
```

### 2. Ошибка отправки изображений
```python
try:
    await bot.send_media_group(...)
except Exception as e:
    logger.error(f"Error sending images: {e}")
    # Отправляем хотя бы текст
```

### 3. Ошибка в callback
```python
try:
    # Обработка callback
except Exception as e:
    logger.error(f"Error in callback: {e}")
    await callback.message.answer("❌ Ошибка")
```

## Конфигурация

В `.env`:

```env
BOT_TOKEN=your_bot_token
ADMIN_CHAT_ID=your_chat_id
```

## Troubleshooting

### Изображения не отправляются

1. Проверьте формат `image_urls` в `ProcessedPost`
2. Убедитесь, что base64 корректный
3. Проверьте доступность URL изображений

### Кнопки не работают

1. Убедитесь, что `FSMContext` передан в handler
2. Проверьте, что роутер зарегистрирован в `main.py`
3. Проверьте логи на ошибки

### FSM не работает

1. Убедитесь, что storage настроен в боте:
   ```python
   from aiogram.fsm.storage.memory import MemoryStorage
   bot = Bot(token=config.BOT_TOKEN)
   dp = Dispatcher(storage=MemoryStorage())
   ```

### Уведомления не приходят

1. Проверьте `ADMIN_CHAT_ID` в конфиге
2. Убедитесь, что бот запущен
3. Проверьте, что `send_post_for_approval()` вызывается в worker
4. Проверьте логи Celery worker

## Следующие шаги

- [ ] Добавить планировщик публикации
- [ ] Реализовать публикацию в Instagram
- [ ] Добавить аналитику постов
- [ ] Интеграция с Instagram Graph API
