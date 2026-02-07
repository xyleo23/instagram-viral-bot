"""
Тестовый скрипт для проверки работы SQLAlchemy моделей.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from app.config import get_config
from app.models import (
    init_db,
    create_tables,
    get_session,
    OriginalPost,
    PostStatus,
    ProcessedPost,
    ProcessedStatus,
    ApprovalHistory,
    DecisionType,
)
from app.utils.logger import setup_logger


async def test_original_post():
    """Тест создания и чтения OriginalPost."""
    print("\n📝 Testing OriginalPost...")
    
    async with get_session() as session:
        # Создание
        post = OriginalPost(
            external_id="test_123456",
            author="test_user",
            author_url="https://instagram.com/test_user",
            text="This is a test post with some content.",
            likes=10000,
            comments=500,
            engagement=0.05,
            post_url="https://instagram.com/p/test_123456",
            posted_at=datetime.utcnow(),
            status=PostStatus.PARSING
        )
        session.add(post)
        await session.commit()
        print(f"✅ Created: {post}")
        
        # Чтение
        result = await session.execute(
            select(OriginalPost).where(OriginalPost.external_id == "test_123456")
        )
        found_post = result.scalar_one()
        print(f"✅ Found: {found_post}")
        
        # Методы
        print(f"   - Is viral: {found_post.is_viral()}")
        print(f"   - Days old: {found_post.days_old()}")
        print(f"   - Is fresh: {found_post.is_fresh()}")
        
        return found_post.id


async def test_processed_post(original_post_id: int):
    """Тест создания ProcessedPost."""
    print("\n🤖 Testing ProcessedPost...")
    
    async with get_session() as session:
        processed = ProcessedPost(
            original_post_id=original_post_id,
            title="Test Title",
            caption="This is a rewritten caption for Instagram.",
            hashtags="#test #instagram #viral",
            slides=["Slide 1", "Slide 2", "Slide 3"],
            slides_count=3,
            ai_model="anthropic/claude-3.5-sonnet",
            tokens_used=1500,
            cost_usd=0.05,
            image_urls=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
            status=ProcessedStatus.PENDING_APPROVAL
        )
        session.add(processed)
        await session.commit()
        print(f"✅ Created: {processed}")
        
        # Методы
        print(f"   - Full caption:\n{processed.get_full_caption()}")
        print(f"   - Telegram preview: {processed.get_telegram_preview()}")
        
        return processed.id


async def test_approval_history(processed_post_id: int):
    """Тест создания ApprovalHistory."""
    print("\n👍 Testing ApprovalHistory...")
    
    async with get_session() as session:
        approval = ApprovalHistory(
            processed_post_id=processed_post_id,
            user_id=123456789,
            username="admin_user",
            decision=DecisionType.APPROVED,
            comment="Looks good!",
            timestamp=datetime.utcnow()
        )
        session.add(approval)
        await session.commit()
        print(f"✅ Created: {approval}")
        print(f"   - Is approved: {approval.is_approved()}")


async def test_relations(original_post_id: int):
    """Тест связей между моделями."""
    print("\n🔗 Testing Relations...")
    
    from sqlalchemy.orm import selectinload
    
    async with get_session() as session:
        # Получить оригинальный пост со всеми обработанными версиями
        result = await session.execute(
            select(OriginalPost)
            .where(OriginalPost.id == original_post_id)
            .options(selectinload(OriginalPost.processed_posts))
        )
        original = result.scalar_one()
        
        print(f"✅ Original post: {original.author}")
        print(f"   - Processed versions: {len(original.processed_posts)}")
        
        for processed in original.processed_posts:
            print(f"     - {processed.title} ({processed.status.value})")


async def cleanup():
    """Очистка тестовых данных."""
    print("\n🧹 Cleaning up test data...")
    
    async with get_session() as session:
        # Удаление тестового поста (cascade удалит связанные записи)
        result = await session.execute(
            select(OriginalPost).where(OriginalPost.external_id == "test_123456")
        )
        post = result.scalar_one_or_none()
        
        if post:
            await session.delete(post)
            await session.commit()
            print("✅ Test data cleaned up")


async def main():
    """Главная функция."""
    print("=" * 60)
    print("🧪 SQLAlchemy Models Test Suite")
    print("=" * 60)
    
    # Настройка
    config = get_config()
    setup_logger(config.LOG_FILE, "WARNING")  # Меньше логов для теста
    
    print(f"\n📍 Database URL: {config.get_database_url()}")
    
    # Инициализация
    init_db(config.get_database_url())
    
    try:
        # Тесты
        original_id = await test_original_post()
        processed_id = await test_processed_post(original_id)
        await test_approval_history(processed_id)
        await test_relations(original_id)
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Очистка
        await cleanup()


if __name__ == "__main__":
    asyncio.run(main())
