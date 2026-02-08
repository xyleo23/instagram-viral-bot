"""
Сервис генерации изображений для слайдов карусели.
Простой вариант: белый фон + чёрный текст по центру (PIL/Pillow).
"""
import asyncio
import os
from pathlib import Path
from typing import List, Optional

from loguru import logger
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select

from app.models.base import async_session_maker
from app.models.processed_post import ProcessedPost


class ImageGenerator:
    """
    Генерирует изображения для слайдов карусели.
    Белый фон, чёрный текст по центру.
    """

    DEFAULT_WIDTH = 1080
    DEFAULT_HEIGHT = 1080
    OUTPUT_DIR = "carousel_images"

    def __init__(
        self,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        output_dir: Optional[str] = None,
    ) -> None:
        self.width = width
        self.height = height
        self.output_dir = Path(output_dir or self.OUTPUT_DIR)

    async def generate_slide_images(self, post_id: int) -> List[str]:
        """
        Генерирует изображения для слайдов поста.

        Args:
            post_id: ID ProcessedPost

        Returns:
            Список путей к сгенерированным файлам
        """
        async with async_session_maker() as session:
            stmt = select(ProcessedPost).where(ProcessedPost.id == post_id)
            result = await session.execute(stmt)
            post = result.scalar_one_or_none()

        if not post:
            logger.error(f"ProcessedPost {post_id} not found")
            return []

        slides: List[str] = post.slides or []
        if not slides:
            logger.warning(f"Post {post_id} has no slides")
            return []

        self.output_dir.mkdir(parents=True, exist_ok=True)
        post_dir = self.output_dir / f"post_{post_id}"
        post_dir.mkdir(parents=True, exist_ok=True)

        paths: List[str] = []
        for idx, slide_text in enumerate(slides):
            try:
                filepath = await asyncio.to_thread(
                    self._create_slide,
                    text=slide_text,
                    post_id=post_id,
                    slide_idx=idx,
                    output_dir=post_dir,
                )
                paths.append(str(filepath))
                logger.debug(f"Generated slide {idx + 1}/{len(slides)} for post {post_id}")
            except Exception as e:
                logger.exception(f"Error generating slide {idx + 1} for post {post_id}: {e}")
                raise

        logger.info(f"Generated {len(paths)} images for post {post_id}")
        return paths

    def _create_slide(
        self,
        text: str,
        post_id: int,
        slide_idx: int,
        output_dir: Path,
    ) -> Path:
        """
        Создаёт одно изображение: белый фон, чёрный текст по центру.
        """
        img = Image.new("RGB", (self.width, self.height), color="#FFFFFF")
        draw = ImageDraw.Draw(img)

        font_size = 72 if slide_idx == 0 else 48
        font = self._get_font(font_size)

        wrapped_text = self._wrap_text(draw, text, font, self.width - 160)
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align="center")
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2

        draw.multiline_text(
            (x, y),
            wrapped_text,
            fill="#000000",
            font=font,
            align="center",
        )

        filepath = output_dir / f"slide_{slide_idx + 1}.png"
        img.save(filepath, "PNG")
        return filepath

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Возвращает шрифт (системный или default)."""
        candidates = [
            "arial.ttf",
            "Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except OSError:
                    continue
        return ImageFont.load_default()

    def _wrap_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> str:
        """Переносит текст по ширине."""
        words = text.split()
        lines: List[str] = []
        current: List[str] = []

        for word in words:
            test_line = " ".join(current + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]

        if current:
            lines.append(" ".join(current))
        return "\n".join(lines)
