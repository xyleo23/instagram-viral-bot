"""
Сервис генерации карусельных изображений через Orshot API или локально через Pillow.
"""
import asyncio
import random
from typing import List, Optional, Tuple, Dict, Any
from io import BytesIO
import aiohttp
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
import colorsys

from app.config import get_config


class CarouselGenerator:
    """Сервис генерации карусельных изображений."""
    
    # Палитра цветов в стиле @theivansergeev (минимализм)
    COLOR_PALETTE = {
        "beige": "#F5F5DC",
        "light_gray": "#E8E8E8",
        "dark_blue": "#2C3E50",
        "slate": "#34495E",
        "off_white": "#ECF0F1",
        "soft_gray": "#95A5A6",
        "black": "#1A1A1A",
        "white": "#FFFFFF",
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        use_local: bool = False
    ):
        """
        Инициализация генератора.
        
        Args:
            api_key: Orshot API ключ (если используем API)
            use_local: Использовать локальную генерацию через Pillow
        """
        self.api_key = api_key
        self.use_local = use_local or not api_key
        self.base_url = "https://api.orshot.com/v1"
        
        self._session: Optional[aiohttp.ClientSession] = None
        
        if self.use_local:
            logger.info("Using local image generation (Pillow)")
        else:
            logger.info("Using Orshot API for image generation")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает или создает HTTP сессию."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=120)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Закрывает HTTP сессию."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def generate(
        self,
        slides: List[str],
        background_style: str = "random",
        width: int = 1080,
        height: int = 1080
    ) -> List[str]:
        """
        Генерирует карусель изображений.
        
        Args:
            slides: Список текстов для каждого слайда
            background_style: Стиль фона ('random', 'gradient', 'solid')
            width: Ширина изображения в пикселях
            height: Высота изображения в пикселях
        
        Returns:
            Список URL или base64 изображений
        """
        logger.info(f"Generating {len(slides)} carousel images")
        
        if self.use_local:
            return await self._generate_local(slides, width, height)
        else:
            return await self._generate_api(slides, width, height)
    
    async def _generate_local(
        self,
        slides: List[str],
        width: int,
        height: int
    ) -> List[str]:
        """
        Генерирует изображения локально через Pillow.
        
        Returns:
            Список путей к файлам или base64
        """
        images = []
        
        for idx, slide_text in enumerate(slides):
            try:
                # 1. Выбрать цвет фона
                bg_color = self._pick_random_color()
                
                # 2. Определить цвет текста (контрастный)
                text_color = self._get_contrast_color(bg_color)
                
                # 3. Размер шрифта (первый слайд крупнее)
                font_size = 72 if idx == 0 else 48
                
                # 4. Создать изображение
                image_data = await self._create_image_pillow(
                    text=slide_text,
                    bg_color=bg_color,
                    text_color=text_color,
                    font_size=font_size,
                    width=width,
                    height=height
                )
                
                images.append(image_data)
                logger.debug(f"Generated slide {idx + 1}/{len(slides)}")
                
            except Exception as e:
                logger.error(f"Error generating slide {idx + 1}: {e}")
                # Fallback: простое изображение
                fallback = await self._create_fallback_image(
                    slide_text, width, height
                )
                images.append(fallback)
        
        logger.info(f"Generated {len(images)} images locally")
        return images
    
    async def _generate_api(
        self,
        slides: List[str],
        width: int,
        height: int
    ) -> List[str]:
        """
        Генерирует изображения через Orshot API.
        
        Returns:
            Список URL изображений
        """
        # Создаем задачи для параллельной генерации
        tasks = []
        for idx, slide_text in enumerate(slides):
            bg_color = self._pick_random_color()
            text_color = self._get_contrast_color(bg_color)
            font_size = 72 if idx == 0 else 48
            
            task = self._generate_single_api(
                text=slide_text,
                bg_color=bg_color,
                text_color=text_color,
                font_size=font_size,
                width=width,
                height=height
            )
            tasks.append(task)
        
        # Параллельная генерация
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка результатов
        images = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error generating slide {idx + 1}: {result}")
                # Fallback на локальную генерацию
                fallback = await self._create_fallback_image(
                    slides[idx], width, height
                )
                images.append(fallback)
            else:
                images.append(result)
        
        logger.info(f"Generated {len(images)} images via API")
        return images
    
    async def _generate_single_api(
        self,
        text: str,
        bg_color: str,
        text_color: str,
        font_size: int,
        width: int,
        height: int
    ) -> str:
        """
        Генерирует одно изображение через Orshot API.
        
        Returns:
            URL изображения
        """
        session = await self._get_session()
        
        payload = {
            "width": width,
            "height": height,
            "background_color": bg_color.replace("#", ""),
            "text": text,
            "text_color": text_color.replace("#", ""),
            "font_size": font_size,
            "font_family": "Inter",  # Современный шрифт
            "text_align": "center",
            "padding": 80,
            "format": "png"
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/generate"
        
        async with session.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["url"]
    
    async def _create_image_pillow(
        self,
        text: str,
        bg_color: str,
        text_color: str,
        font_size: int,
        width: int,
        height: int
    ) -> str:
        """
        Создает изображение локально через Pillow.
        
        Returns:
            Base64 строка изображения
        """
        # Создаем изображение
        img = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Загружаем шрифт (встроенный или системный)
        try:
            # Пытаемся использовать Arial/Helvetica
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                # Fallback на стандартный шрифт
                font = ImageFont.load_default()
        
        # Перенос текста на новые строки
        wrapped_text = self._wrap_text(text, font, width - 160, draw)
        
        # Вычисляем размеры текста
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align="center")
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Центрируем текст
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Рисуем текст
        draw.multiline_text(
            (x, y),
            wrapped_text,
            fill=text_color,
            font=font,
            align="center"
        )
        
        # Сохраняем в base64
        import base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    def _wrap_text(
        self,
        text: str,
        font,
        max_width: int,
        draw: ImageDraw.Draw
    ) -> str:
        """
        Переносит текст на новые строки.
        
        Args:
            text: Исходный текст
            font: Шрифт PIL
            max_width: Максимальная ширина
            draw: ImageDraw объект
        
        Returns:
            Текст с переносами
        """
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    async def _create_fallback_image(
        self,
        text: str,
        width: int,
        height: int
    ) -> str:
        """
        Создает простое fallback изображение.
        
        Returns:
            Base64 строка
        """
        return await self._create_image_pillow(
            text=text[:100],
            bg_color="#ECF0F1",
            text_color="#1A1A1A",
            font_size=48,
            width=width,
            height=height
        )
    
    def _pick_random_color(self) -> str:
        """Выбирает случайный цвет из палитры."""
        return random.choice(list(self.COLOR_PALETTE.values()))
    
    def _get_contrast_color(self, bg_color: str) -> str:
        """
        Определяет контрастный цвет текста для фона.
        
        Использует формулу относительной яркости:
        brightness = (R*299 + G*587 + B*114) / 1000
        
        Args:
            bg_color: Цвет фона в hex (#RRGGBB)
        
        Returns:
            Цвет текста (белый или черный)
        """
        # Парсим hex цвет
        hex_color = bg_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        
        # Вычисляем яркость
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        
        # Если фон темный -> белый текст, иначе черный
        return "#FFFFFF" if brightness < 128 else "#1A1A1A"
    
    def save_images_locally(
        self,
        images: List[str],
        output_dir: str = "carousel_images"
    ) -> List[str]:
        """
        Сохраняет изображения локально (если они в base64).
        
        Args:
            images: Список base64 или URL
            output_dir: Папка для сохранения
        
        Returns:
            Список путей к файлам
        """
        import os
        import base64
        from pathlib import Path
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        
        for idx, img_data in enumerate(images):
            if img_data.startswith("data:image"):
                # Base64 изображение
                img_base64 = img_data.split(",")[1]
                img_bytes = base64.b64decode(img_base64)
                
                filename = f"slide_{idx + 1}.png"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                
                saved_paths.append(filepath)
                logger.info(f"Saved {filepath}")
            else:
                # URL - добавляем как есть
                saved_paths.append(img_data)
        
        return saved_paths


# ==================== USAGE EXAMPLE ====================

async def main():
    """Пример использования Carousel Generator."""
    config = get_config()
    
    # Используем локальную генерацию (Pillow)
    generator = CarouselGenerator(
        api_key=config.ORSHOT_API_KEY if hasattr(config, 'ORSHOT_API_KEY') else None,
        use_local=True  # Локальная генерация
    )
    
    # Тестовые слайды
    test_slides = [
        "7 ошибок которые убивают ваш бизнес",
        "Ошибка #1: Вы не знаете свою целевую аудиторию",
        "Ошибка #2: Нет четкого позиционирования",
        "Ошибка #3: Игнорируете обратную связь клиентов",
        "Ошибка #4: Не инвестируете в маркетинг",
        "Ошибка #5: Пытаетесь охватить всех сразу",
        "Ошибка #6: Не автоматизируете процессы",
        "Ошибка #7: Не следите за конкурентами"
    ]
    
    try:
        print("🎨 Generating carousel images...\n")
        
        images = await generator.generate(
            slides=test_slides,
            background_style="random"
        )
        
        print(f"✅ Generated {len(images)} images\n")
        
        # Сохраняем локально
        saved_paths = generator.save_images_locally(images, "test_carousel")
        
        print("💾 Saved images:")
        for path in saved_paths:
            print(f"  - {path}")
        
    finally:
        await generator.close()


if __name__ == "__main__":
    from app.utils.logger import setup_logger
    setup_logger()
    asyncio.run(main())
