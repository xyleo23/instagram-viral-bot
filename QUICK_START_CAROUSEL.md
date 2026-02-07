# 🎨 Quick Start - Carousel Generator

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install pillow aiohttp loguru
```

> **Примечание**: Pillow уже есть в `requirements.txt`

### 2. Запуск теста

```bash
python -m scripts.test_carousel
```

**Ожидаемый результат**:

```
🎨 Testing Carousel Generator

Generating 8 slides...

✅ Generated 8 images!

💾 Saved to ./carousel_output/
  1. carousel_output\slide_1.png
  2. carousel_output\slide_2.png
  ...
  8. carousel_output\slide_8.png

📊 Statistics:
  Slides: 8
  Images: 8
  Format: 1080x1080 PNG
  Style: Minimalist (like @theivansergeev)
```

### 3. Проверка изображений

```bash
# Windows
dir carousel_output

# Linux/Mac
ls -lh carousel_output/
```

Должны быть 8 PNG файлов размером 13-26 KB каждый.

## 💡 Примеры использования

### Пример 1: Простая генерация

```python
import asyncio
from app.services.carousel_generator import CarouselGenerator

async def main():
    generator = CarouselGenerator(use_local=True)
    
    slides = [
        "Заголовок карусели",
        "Слайд 1: Первый пункт",
        "Слайд 2: Второй пункт"
    ]
    
    images = await generator.generate(slides)
    saved_paths = generator.save_images_locally(images, "my_carousel")
    
    print(f"Создано {len(saved_paths)} изображений")
    await generator.close()

asyncio.run(main())
```

### Пример 2: Кастомные параметры

```python
images = await generator.generate(
    slides=slides,
    background_style="random",  # или "gradient", "solid"
    width=1080,
    height=1080
)
```

### Пример 3: Через Orshot API

```python
from app.config import get_config

config = get_config()
generator = CarouselGenerator(
    api_key=config.ORSHOT_API_KEY,
    use_local=False  # Использовать API вместо Pillow
)

images = await generator.generate(slides)
```

## 🎨 Дизайн

### Палитра цветов (минимализм):

- **Beige**: `#F5F5DC`
- **Light Gray**: `#E8E8E8`
- **Dark Blue**: `#2C3E50`
- **Slate**: `#34495E`
- **Off White**: `#ECF0F1`
- **Soft Gray**: `#95A5A6`
- **Black**: `#1A1A1A`
- **White**: `#FFFFFF`

### Особенности:

- ✅ Случайный выбор цвета фона из палитры
- ✅ Автоматический контрастный цвет текста
- ✅ Первый слайд: шрифт 72px (заголовок)
- ✅ Остальные слайды: шрифт 48px
- ✅ Автоматический перенос текста на новые строки
- ✅ Размер: 1080x1080 (оптимально для Instagram)

## 🔧 Интеграция с ботом

### В handlers/carousel.py:

```python
from aiogram import types
from app.services.carousel_generator import CarouselGenerator

async def generate_carousel_handler(message: types.Message):
    """Генерирует карусель из текста."""
    
    # Парсим текст на слайды
    text = message.text.replace("/carousel", "").strip()
    slides = text.split("\n\n")  # Разделение по двойному переносу
    
    if len(slides) < 2:
        await message.answer("❌ Нужно минимум 2 слайда")
        return
    
    # Генерируем изображения
    generator = CarouselGenerator(use_local=True)
    
    try:
        await message.answer("🎨 Генерирую карусель...")
        
        images = await generator.generate(slides)
        saved_paths = generator.save_images_locally(images, "temp_carousel")
        
        # Отправляем в Telegram
        media_group = []
        for path in saved_paths:
            media_group.append(
                types.InputMediaPhoto(media=types.FSInputFile(path))
            )
        
        await message.answer_media_group(media_group)
        await message.answer(f"✅ Создано {len(saved_paths)} слайдов")
        
    finally:
        await generator.close()
```

### Регистрация хендлера:

```python
from aiogram import Router

router = Router()
router.message.register(generate_carousel_handler, Command("carousel"))
```

## 📊 API Reference

### Класс `CarouselGenerator`

#### Инициализация:

```python
generator = CarouselGenerator(
    api_key: Optional[str] = None,  # Orshot API ключ
    use_local: bool = False          # Использовать Pillow
)
```

#### Методы:

```python
# Генерация изображений
await generator.generate(
    slides: List[str],              # Список текстов слайдов
    background_style: str = "random",  # "random", "gradient", "solid"
    width: int = 1080,              # Ширина в пикселях
    height: int = 1080              # Высота в пикселях
) -> List[str]  # Возвращает base64 или URL

# Сохранение локально
generator.save_images_locally(
    images: List[str],              # Список base64/URL
    output_dir: str = "carousel_images"  # Папка для сохранения
) -> List[str]  # Возвращает пути к файлам

# Закрытие сессии
await generator.close()
```

## 🐛 Troubleshooting

### Проблема: UnicodeEncodeError в Windows

**Решение**: Скрипт уже исправлен, использует UTF-8 wrapper:

```python
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### Проблема: Шрифт не найден

**Решение**: Генератор автоматически использует fallback:

```python
try:
    font = ImageFont.truetype("arial.ttf", font_size)
except:
    font = ImageFont.load_default()  # Стандартный шрифт
```

### Проблема: Orshot API не работает

**Решение**: Используйте локальную генерацию:

```python
generator = CarouselGenerator(use_local=True)
```

## ⚡ Производительность

| Параметр | Значение |
|----------|----------|
| Время генерации | ~1 сек для 8 слайдов |
| Размер изображения | 13-26 KB (PNG) |
| Разрешение | 1080x1080 |
| Режим | Параллельный (asyncio) |

## 📝 Конфигурация

### В .env (опционально):

```env
# Orshot API (если используется)
ORSHOT_API_KEY=your_api_key_here
```

### В config.py:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ORSHOT_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
```

## 🎯 Следующие шаги

1. ✅ Запустить тест: `python -m scripts.test_carousel`
2. ✅ Проверить изображения в `carousel_output/`
3. ✅ Интегрировать с handlers/carousel.py
4. ✅ Добавить команду `/carousel` в бота
5. ✅ Подключить к AI Rewriter для автоматической генерации слайдов

## 📚 Дополнительные ресурсы

- **Полная документация**: `CAROUSEL_GENERATOR_SUMMARY.md`
- **Чеклист**: `CAROUSEL_CHECKLIST.md`
- **Код сервиса**: `app/services/carousel_generator.py`
- **Тестовый скрипт**: `scripts/test_carousel.py`

---

**Статус**: ✅ **Готово к использованию**

**Дата**: 30.01.2026

**Автор**: Carousel Generator Service
