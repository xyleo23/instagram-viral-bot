"""
Примеры использования SQLAlchemy моделей.

Этот файл содержит практические примеры работы с моделями БД.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.config import get_config
from app.models import (
    init_db,
    get_session,
    OriginalPost,
    PostStatus,
    ProcessedPost,
    ProcessedStatus,
    ApprovalHistory,
    DecisionType,
)


# ==================== СОЗДАНИЕ ====================

async def example_create_original_post():
    """Пример создания оригинального поста."""
    print("\n📝 Creating OriginalPost...")
    
    async with get_session() as session:
        post = OriginalPost(
            external_id="example_123",
            author="viral_account",
            author_url="https://instagram.com/viral_account",
            text="Amazing content that went viral! 🚀",
            likes=15000,
            comments=850,
            engagement=0.08,
            post_url="https://instagram.com/p/example_123",
            posted_at=datetime.utcnow() - timedelta(hours=12),
            status=PostStatus.FILTERED
        )
        session.add(post)
        await session.commit()
        
        print(f"✅ Created: {post}")
        return post.id


async def example_create_processed_post(original_post_id: int):
    """Пример создания обработанного поста."""
    print("\n🤖 Creating ProcessedPost...")
    
    async with get_session() as session:
        processed = ProcessedPost(
            original_post_id=original_post_id,
            title="Как достичь успеха в бизнесе",
            caption="Секреты успешных предпринимателей, которые изменят вашу жизнь...",
            hashtags="#бизнес #успех #мотивация #предприниматель",
            slides=[
                "Слайд 1: Введение",
                "Слайд 2: Главный секрет",
                "Слайд 3: Практические советы",
                "Слайд 4: Заключение"
            ],
            slides_count=4,
            ai_model="anthropic/claude-3.5-sonnet",
            tokens_used=2500,
            cost_usd=0.075,
            image_urls=[
                "https://example.com/slide1.jpg",
                "https://example.com/slide2.jpg",
                "https://example.com/slide3.jpg",
                "https://example.com/slide4.jpg"
            ],
            status=ProcessedStatus.PENDING_APPROVAL
        )
        session.add(processed)
        await session.commit()
        
        print(f"✅ Created: {processed}")
        return processed.id


async def example_create_approval(processed_post_id: int):
    """Пример создания записи одобрения."""
    print("\n👍 Creating ApprovalHistory...")
    
    async with get_session() as session:
        approval = ApprovalHistory(
            processed_post_id=processed_post_id,
            user_id=123456789,
            username="admin_user",
            decision=DecisionType.APPROVED,
            comment="Отличный контент! Публикуем.",
            timestamp=datetime.utcnow()
        )
        session.add(approval)
        await session.commit()
        
        print(f"✅ Created: {approval}")


# ==================== ЧТЕНИЕ ====================

async def example_get_viral_posts():
    """Пример получения вирусных постов."""
    print("\n🔥 Getting viral posts (likes >= 10000)...")
    
    async with get_session() as session:
        result = await session.execute(
            select(OriginalPost)
            .where(OriginalPost.likes >= 10000)
            .order_by(OriginalPost.likes.desc())
        )
        posts = result.scalars().all()
        
        print(f"✅ Found {len(posts)} viral posts:")
        for post in posts:
            print(f"   - @{post.author}: {post.likes} likes")


async def example_get_pending_approval():
    """Пример получения постов, ожидающих одобрения."""
    print("\n⏳ Getting posts pending approval...")
    
    async with get_session() as session:
        result = await session.execute(
            select(ProcessedPost)
            .where(ProcessedPost.status == ProcessedStatus.PENDING_APPROVAL)
            .order_by(ProcessedPost.created_at.desc())
        )
        posts = result.scalars().all()
        
        print(f"✅ Found {len(posts)} posts pending approval:")
        for post in posts:
            print(f"   - {post.title}")


async def example_get_post_with_relations():
    """Пример получения поста со всеми связями."""
    print("\n🔗 Getting post with all relations...")
    
    async with get_session() as session:
        result = await session.execute(
            select(OriginalPost)
            .options(
                selectinload(OriginalPost.processed_posts)
                .selectinload(ProcessedPost.approvals)
            )
            .limit(1)
        )
        post = result.scalar_one_or_none()
        
        if post:
            print(f"✅ Original post: @{post.author}")
            print(f"   - Processed versions: {len(post.processed_posts)}")
            
            for processed in post.processed_posts:
                print(f"     - {processed.title} ({processed.status.value})")
                print(f"       Approvals: {len(processed.approvals)}")
                
                for approval in processed.approvals:
                    print(f"         - {approval.decision.value} by {approval.username}")


# ==================== ОБНОВЛЕНИЕ ====================

async def example_update_post_status():
    """Пример обновления статуса поста."""
    print("\n🔄 Updating post status...")
    
    async with get_session() as session:
        result = await session.execute(
            select(OriginalPost)
            .where(OriginalPost.status == PostStatus.FILTERED)
            .limit(1)
        )
        post = result.scalar_one_or_none()
        
        if post:
            old_status = post.status
            post.status = PostStatus.PROCESSING
            await session.commit()
            
            print(f"✅ Updated post status: {old_status.value} → {post.status.value}")


async def example_approve_post():
    """Пример одобрения поста."""
    print("\n✅ Approving post...")
    
    async with get_session() as session:
        # Найти пост, ожидающий одобрения
        result = await session.execute(
            select(ProcessedPost)
            .where(ProcessedPost.status == ProcessedStatus.PENDING_APPROVAL)
            .limit(1)
        )
        processed = result.scalar_one_or_none()
        
        if processed:
            # Обновить статус
            processed.status = ProcessedStatus.APPROVED
            
            # Создать запись в истории
            approval = ApprovalHistory(
                processed_post_id=processed.id,
                user_id=987654321,
                username="approver",
                decision=DecisionType.APPROVED,
                timestamp=datetime.utcnow()
            )
            session.add(approval)
            
            await session.commit()
            print(f"✅ Post approved: {processed.title}")


# ==================== СЛОЖНЫЕ ЗАПРОСЫ ====================

async def example_statistics_by_author():
    """Пример получения статистики по авторам."""
    print("\n📊 Getting statistics by author...")
    
    async with get_session() as session:
        result = await session.execute(
            select(
                OriginalPost.author,
                func.count(OriginalPost.id).label('posts_count'),
                func.avg(OriginalPost.likes).label('avg_likes'),
                func.max(OriginalPost.likes).label('max_likes'),
                func.sum(OriginalPost.comments).label('total_comments')
            )
            .group_by(OriginalPost.author)
            .order_by(func.count(OriginalPost.id).desc())
        )
        stats = result.all()
        
        print(f"✅ Statistics for {len(stats)} authors:")
        for stat in stats:
            print(f"   - @{stat.author}:")
            print(f"     Posts: {stat.posts_count}")
            print(f"     Avg likes: {stat.avg_likes:.0f}")
            print(f"     Max likes: {stat.max_likes}")
            print(f"     Total comments: {stat.total_comments}")


async def example_recent_posts():
    """Пример получения свежих постов (последние 24 часа)."""
    print("\n🕐 Getting recent posts (last 24 hours)...")
    
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    async with get_session() as session:
        result = await session.execute(
            select(OriginalPost)
            .where(OriginalPost.posted_at >= yesterday)
            .order_by(OriginalPost.posted_at.desc())
        )
        posts = result.scalars().all()
        
        print(f"✅ Found {len(posts)} recent posts:")
        for post in posts:
            age_hours = (datetime.utcnow() - post.posted_at).total_seconds() / 3600
            print(f"   - @{post.author}: {age_hours:.1f}h ago, {post.likes} likes")


async def example_expensive_processing():
    """Пример получения самых дорогих обработок."""
    print("\n💰 Getting most expensive processing...")
    
    async with get_session() as session:
        result = await session.execute(
            select(ProcessedPost)
            .order_by(ProcessedPost.cost_usd.desc())
            .limit(5)
        )
        posts = result.scalars().all()
        
        total_cost = sum(p.cost_usd for p in posts)
        
        print(f"✅ Top 5 expensive processing (total: ${total_cost:.3f}):")
        for post in posts:
            print(f"   - {post.title[:40]}...")
            print(f"     Cost: ${post.cost_usd:.3f}, Tokens: {post.tokens_used}")


# ==================== МЕТОДЫ МОДЕЛЕЙ ====================

async def example_model_methods():
    """Пример использования методов моделей."""
    print("\n🛠️ Testing model methods...")
    
    async with get_session() as session:
        # OriginalPost методы
        result = await session.execute(select(OriginalPost).limit(1))
        original = result.scalar_one_or_none()
        
        if original:
            print(f"✅ OriginalPost methods:")
            print(f"   - is_viral(): {original.is_viral()}")
            print(f"   - days_old(): {original.days_old()}")
            print(f"   - is_fresh(): {original.is_fresh()}")
            print(f"   - to_dict(): {list(original.to_dict().keys())}")
        
        # ProcessedPost методы
        result = await session.execute(select(ProcessedPost).limit(1))
        processed = result.scalar_one_or_none()
        
        if processed:
            print(f"\n✅ ProcessedPost methods:")
            print(f"   - get_full_caption(): {len(processed.get_full_caption())} chars")
            print(f"   - get_telegram_preview(): {len(processed.get_telegram_preview())} chars")
            print(f"   - to_dict(): {list(processed.to_dict().keys())}")


# ==================== УДАЛЕНИЕ ====================

async def example_cascade_delete():
    """Пример каскадного удаления."""
    print("\n🗑️ Testing cascade delete...")
    
    async with get_session() as session:
        # Создать тестовый пост
        post = OriginalPost(
            external_id="delete_test",
            author="test",
            author_url="https://instagram.com/test",
            text="Test post for deletion",
            likes=1000,
            post_url="https://instagram.com/p/delete_test",
            posted_at=datetime.utcnow()
        )
        session.add(post)
        await session.commit()
        post_id = post.id
        
        # Создать связанный ProcessedPost
        processed = ProcessedPost(
            original_post_id=post_id,
            title="Test",
            caption="Test",
            hashtags="#test",
            slides=["Test"],
            slides_count=1,
            ai_model="test",
            image_urls=[]
        )
        session.add(processed)
        await session.commit()
        
        print(f"✅ Created test post with id={post_id}")
        
        # Удалить оригинальный пост
        await session.delete(post)
        await session.commit()
        
        print(f"✅ Deleted original post (cascade should delete processed post too)")
        
        # Проверить, что ProcessedPost тоже удален
        result = await session.execute(
            select(ProcessedPost).where(ProcessedPost.original_post_id == post_id)
        )
        remaining = result.scalar_one_or_none()
        
        if remaining is None:
            print(f"✅ Cascade delete worked! ProcessedPost was deleted too.")
        else:
            print(f"❌ Cascade delete failed! ProcessedPost still exists.")


# ==================== MAIN ====================

async def main():
    """Запуск всех примеров."""
    print("=" * 70)
    print("📚 SQLAlchemy Models Usage Examples")
    print("=" * 70)
    
    # Инициализация
    config = get_config()
    init_db(config.get_database_url())
    
    try:
        # Создание
        original_id = await example_create_original_post()
        processed_id = await example_create_processed_post(original_id)
        await example_create_approval(processed_id)
        
        # Чтение
        await example_get_viral_posts()
        await example_get_pending_approval()
        await example_get_post_with_relations()
        
        # Обновление
        await example_update_post_status()
        await example_approve_post()
        
        # Сложные запросы
        await example_statistics_by_author()
        await example_recent_posts()
        await example_expensive_processing()
        
        # Методы моделей
        await example_model_methods()
        
        # Удаление
        await example_cascade_delete()
        
        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
