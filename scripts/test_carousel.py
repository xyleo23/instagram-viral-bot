"""
Тестовый скрипт для Carousel Generator.
"""
import asyncio
from app.config import get_config
from app.services.carousel_generator import CarouselGenerator
from app.utils.logger import setup_logger


async def main():
    """Тестирует Carousel Generator."""
    import sys
    import io
    
    # Исправляем кодировку для Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    config = get_config()
    setup_logger(config.LOG_FILE, "DEBUG")
    
    print("🎨 Testing Carousel Generator\n")
    
    # Тестовые слайды
    slides = [
        "Как я заработал 1M на AI за месяц",
        "Шаг 1: Нашел нишу с минимальной конкуренцией",
        "Шаг 2: Создал уникальный продукт за 2 недели",
        "Шаг 3: Запустил таргетированную рекламу",
        "Шаг 4: Автоматизировал все процессы",
        "Шаг 5: Масштабировал на других рынках",
        "Результат: 1M+ дохода и 5000+ клиентов",
        "Главное: начать делать, а не думать"
    ]
    
    # Локальная генерация (работает без API ключей)
    generator = CarouselGenerator(use_local=True)
    
    try:
        print(f"Generating {len(slides)} slides...\n")
        
        images = await generator.generate(
            slides=slides,
            background_style="random",
            width=1080,
            height=1080
        )
        
        print(f"\n✅ Generated {len(images)} images!")
        
        # Сохраняем
        output_dir = "carousel_output"
        saved_paths = generator.save_images_locally(images, output_dir)
        
        print(f"\n💾 Saved to ./{output_dir}/")
        for i, path in enumerate(saved_paths, 1):
            print(f"  {i}. {path}")
        
        print(f"\n📊 Statistics:")
        print(f"  Slides: {len(slides)}")
        print(f"  Images: {len(images)}")
        print(f"  Format: 1080x1080 PNG")
        print(f"  Style: Minimalist (like @theivansergeev)")
        
    finally:
        await generator.close()


if __name__ == "__main__":
    asyncio.run(main())
