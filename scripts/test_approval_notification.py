"""
Тестовый скрипт для проверки отправки уведомлений об одобрении.
Создает тестовый ProcessedPost и отправляет его админу.
"""
import asyncio
from aiogram import Bot
from loguru import logger

from app.config import get_config
from app.models import init_db, get_session, ProcessedPost, OriginalPost
from app.bot.handlers.approval import send_post_for_approval
from sqlalchemy import select


async def create_test_post() -> int:
    """
    Создает тестовый ProcessedPost для проверки уведомлений.
    
    Returns:
        ID созданного ProcessedPost
    """
    config = get_config()
    init_db(config.get_database_url())
    
    # Находим любой обработанный пост или создаем тестовый
    async with get_session() as session:
        result = await session.execute(
            select(ProcessedPost)
            .limit(1)
        )
        existing_post = result.scalar_one_or_none()
        
        if existing_post:
            logger.info(f"Using existing ProcessedPost ID: {existing_post.id}")
            return existing_post.id
        
        # Создаем тестовый OriginalPost
        logger.info("Creating test OriginalPost...")
        original = OriginalPost(
            shortcode="test_12345",
            author="testuser",
            text="Тестовый пост для проверки системы уведомлений",
            likes=5000,
            comments=120,
            post_url="https://instagram.com/p/test_12345",
            image_urls=["https://via.placeholder.com/1080"],
            timestamp="2025-01-30T12:00:00Z"
        )
        session.add(original)
        await session.commit()
        await session.refresh(original)
        
        # Создаем тестовый ProcessedPost
        logger.info("Creating test ProcessedPost...")
        processed = ProcessedPost(
            original_post_id=original.id,
            title="🚀 Тестовый заголовок: Как достичь успеха",
            caption=(
                "Это тестовый пост для проверки системы одобрения.\n\n"
                "✅ Проверяем отправку медиа-группы\n"
                "✅ Проверяем форматирование текста\n"
                "✅ Проверяем работу кнопок\n\n"
                "Если вы видите это сообщение, значит все работает!"
            ),
            hashtags="#тест #проверка #бот #успех",
            slides=[
                {"text": "Слайд 1", "background": "#FF6B6B"},
                {"text": "Слайд 2", "background": "#4ECDC4"},
                {"text": "Слайд 3", "background": "#45B7D1"}
            ],
            slides_count=3,
            ai_model="openrouter/anthropic/claude-3.5-sonnet",
            tokens_used=1500,
            cost_usd=0.0075,
            image_urls=[
                "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            ],
            yandex_disk_folder="https://disk.yandex.ru/d/test_folder_123"
        )
        session.add(processed)
        await session.commit()
        await session.refresh(processed)
        
        logger.info(f"Created test ProcessedPost ID: {processed.id}")
        return processed.id


async def test_send_approval():
    """Тестирует отправку уведомления об одобрении."""
    config = get_config()
    
    logger.info("=== Starting Approval Notification Test ===")
    
    # 1. Создаем/получаем тестовый пост
    post_id = await create_test_post()
    
    # 2. Отправляем уведомление
    logger.info(f"Sending approval notification for post {post_id}...")
    bot = Bot(token=config.BOT_TOKEN)
    
    try:
        await send_post_for_approval(bot, post_id)
        logger.success("✅ Notification sent successfully!")
        logger.info(f"Check your Telegram chat (ID: {config.ADMIN_CHAT_ID})")
    except Exception as e:
        logger.error(f"❌ Error sending notification: {e}")
        raise
    finally:
        await bot.session.close()
    
    logger.info("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_send_approval())
