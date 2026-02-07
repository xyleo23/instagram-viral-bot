# 📦 Yandex.Disk Upload Service

Асинхронный сервис для загрузки изображений на Яндекс.Диск с автоматической организацией по датам.

## ✨ Возможности

- ✅ Асинхронная загрузка изображений
- ✅ Поддержка base64 и URL изображений
- ✅ Автоматическое создание папок по датам
- ✅ Получение публичных ссылок
- ✅ Информация о диске (свободное место)
- ✅ Обработка ошибок и лимитов

## 🚀 Быстрый старт

### 1. Получение OAuth токена

1. Перейдите на https://oauth.yandex.ru/
2. Нажмите "Зарегистрировать новое приложение"
3. Заполните форму:
   - Название: Instagram Bot
   - Платформы: Веб-сервисы
   - Права доступа: **Яндекс.Диск REST API** → **Чтение и запись**
4. Получите токен через OAuth URL:
   ```
   https://oauth.yandex.ru/authorize?response_type=token&client_id=YOUR_CLIENT_ID
   ```

### 2. Настройка

Добавьте токен в `.env`:

```env
YANDEX_DISK_TOKEN=y0_AgAAAAA...ваш_токен
```

### 3. Запуск теста

```bash
python scripts/test_yandex_disk.py
```

## 📖 Использование

### Базовый пример

```python
from app.services.yandex_disk import YandexDiskUploader
from app.config import get_config

config = get_config()
uploader = YandexDiskUploader(token=config.YANDEX_DISK_TOKEN)

try:
    # Загрузка изображений
    result = await uploader.upload_images(
        images=[
            "data:image/png;base64,iVBORw0KG...",
            "https://example.com/image.jpg"
        ],
        post_id=12345
    )
    
    print(f"Folder: {result['folder_path']}")
    print(f"Public URL: {result['folder_url']}")
    print(f"Files: {len(result['uploaded_files'])}")
    print(f"Size: {result['total_size_mb']} MB")
    
finally:
    await uploader.close()
```

### Проверка свободного места

```python
disk_info = await uploader.get_disk_info()

print(f"Total: {disk_info['total_gb']} GB")
print(f"Used: {disk_info['used_gb']} GB")
print(f"Free: {disk_info['free_gb']} GB")
```

### Кастомный путь к папке

```python
result = await uploader.upload_images(
    images=images,
    folder_path="/My_Custom_Folder/subfolder"
)
```

## 📁 Структура папок

Автоматически создается структура:

```
/Instagram_Content/
├── 2026-01/
│   ├── post_12345/
│   │   ├── slide_1.png
│   │   ├── slide_2.png
│   │   └── slide_3.png
│   ├── post_12346/
│   └── carousel_20260130_143022/
└── 2026-02/
    └── ...
```

## 🔧 API Reference

### `YandexDiskUploader`

#### `__init__(token: str)`

Инициализация uploader'а.

**Args:**
- `token` - OAuth токен Яндекс.Диска

#### `upload_images(images, folder_path=None, post_id=None) -> dict`

Загружает изображения на Яндекс.Диск.

**Args:**
- `images: List[str]` - Список изображений (base64 или URL)
- `folder_path: Optional[str]` - Путь к папке (если None, генерируется автоматически)
- `post_id: Optional[int]` - ID поста (для имени папки)

**Returns:**
```python
{
    "folder_path": "/Instagram_Content/2026-01/post_12345",
    "folder_url": "https://disk.yandex.ru/d/...",
    "uploaded_files": [
        "/Instagram_Content/2026-01/post_12345/slide_1.png",
        "/Instagram_Content/2026-01/post_12345/slide_2.png"
    ],
    "total_size_mb": 2.45
}
```

#### `get_disk_info() -> dict`

Получает информацию о диске.

**Returns:**
```python
{
    "total_space": 10737418240,  # bytes
    "used_space": 5368709120,    # bytes
    "free_space": 5368709120,    # bytes
    "total_gb": 10.0,
    "used_gb": 5.0,
    "free_gb": 5.0
}
```

#### `get_public_url(path: str) -> str`

Получает публичную ссылку на файл/папку.

**Args:**
- `path: str` - Путь к ресурсу на Яндекс.Диске

**Returns:**
- `str` - Публичная ссылка

#### `close()`

Закрывает HTTP сессию. Всегда вызывайте в `finally` блоке.

## ⚠️ Обработка ошибок

### Нехватка места

```python
try:
    result = await uploader.upload_images(images)
except aiohttp.ClientResponseError as e:
    if e.status == 507:
        print("Insufficient storage on Yandex.Disk")
```

### Лимиты API

Яндекс.Диск имеет лимиты:
- **10 запросов в секунду** на один токен
- **100 МБ** максимальный размер файла через REST API

Сервис автоматически обрабатывает эти лимиты через `aiohttp.ClientTimeout`.

### Невалидный токен

```python
try:
    disk_info = await uploader.get_disk_info()
except aiohttp.ClientResponseError as e:
    if e.status == 401:
        print("Invalid or expired Yandex.Disk token")
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Основной тест
python scripts/test_yandex_disk.py

# Встроенный пример
python -m app.services.yandex_disk
```

### Ожидаемый вывод

```
☁️  Testing Yandex.Disk Uploader

💾 Disk Information:
   Total: 10.0 GB
   Used: 5.23 GB (5,614,592,000 bytes)
   Free: 4.77 GB

📤 Uploading 8 images to Yandex.Disk...

✅ Upload Successful!

============================================================
📁 Folder Path: /Instagram_Content/2026-01/post_999
🔗 Public URL: https://disk.yandex.ru/d/abc123xyz
📊 Uploaded Files: 8
💾 Total Size: 2.45 MB
============================================================

Uploaded files:
  ✓ /Instagram_Content/2026-01/post_999/slide_1.png
  ✓ /Instagram_Content/2026-01/post_999/slide_2.png
  ...
```

## 🔗 Интеграция с другими сервисами

### С Carousel Generator

```python
from app.services.carousel_generator import CarouselGenerator
from app.services.yandex_disk import YandexDiskUploader

# 1. Генерируем карусель
generator = CarouselGenerator(api_key=config.ORSHOT_API_KEY)
slides = await generator.generate_carousel(post_data)

# 2. Загружаем на Яндекс.Диск
uploader = YandexDiskUploader(token=config.YANDEX_DISK_TOKEN)
result = await uploader.upload_images(
    images=slides,
    post_id=post_data["id"]
)

print(f"Public URL: {result['folder_url']}")
```

### С Telegram Bot

```python
from aiogram import types

@router.message(Command("upload"))
async def upload_handler(message: types.Message):
    # Загружаем изображения
    result = await uploader.upload_images(images, post_id=123)
    
    # Отправляем ссылку пользователю
    await message.answer(
        f"✅ Uploaded {len(result['uploaded_files'])} files\n"
        f"🔗 {result['folder_url']}"
    )
```

## 📝 Логирование

Сервис использует `loguru` для логирования:

```
2026-01-30 14:30:15 | INFO     | yandex_disk:upload_images:67 - Uploading 8 images to Yandex.Disk
2026-01-30 14:30:16 | INFO     | yandex_disk:_create_folder:129 - Folder created: /Instagram_Content/2026-01/post_999
2026-01-30 14:30:17 | INFO     | yandex_disk:upload_images:90 - Uploaded slide_1.png (312.5 KB)
2026-01-30 14:30:18 | INFO     | yandex_disk:upload_images:90 - Uploaded slide_2.png (298.1 KB)
...
2026-01-30 14:30:25 | INFO     | yandex_disk:upload_images:107 - Upload completed: 8 files, 2.45 MB
```

## 🐛 Troubleshooting

### Проблема: "Invalid token"

**Решение:** Проверьте токен:
1. Убедитесь, что токен не истек
2. Проверьте права доступа (должен быть доступ к Яндекс.Диску)
3. Перегенерируйте токен

### Проблема: "Folder already exists"

**Решение:** Это нормально, сервис автоматически обрабатывает существующие папки (статус 409).

### Проблема: "Insufficient storage"

**Решение:**
1. Очистите место на Яндекс.Диске
2. Увеличьте объем диска
3. Используйте другой аккаунт

### Проблема: Медленная загрузка

**Решение:**
1. Проверьте размер изображений (оптимизируйте если > 1 МБ)
2. Увеличьте `timeout` в `_get_session()`
3. Загружайте изображения батчами

## 📚 Полезные ссылки

- [Yandex.Disk REST API](https://yandex.ru/dev/disk/rest/)
- [OAuth Yandex](https://oauth.yandex.ru/)
- [Лимиты API](https://yandex.ru/dev/disk/api/concepts/limits.html)

## ✅ Checklist

- [x] Асинхронный класс `YandexDiskUploader`
- [x] Интеграция с Yandex.Disk REST API
- [x] Автоматическое создание папок по датам
- [x] Загрузка изображений (base64 и URL)
- [x] Получение публичных ссылок
- [x] Обработка ошибок (нехватка места, лимиты)
- [x] Тестовый скрипт `test_yandex_disk.py`
- [x] Документация
