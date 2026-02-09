"""
Тестирование Celery задач напрямую (без broker).
"""
import asyncio
from app.config import get_config
from app.utils.logger import setup_logger
from app.models import init_db
from app.workers.tasks.parsing import parse_specific_account
from app.workers.tasks.processing import process_single_post


async def main():
    """Тестирует Celery задачи напрямую."""
    config = get_config()
    setup_logger(config.LOG_FILE, "DEBUG")
    
    # Инициализация БД
    init_db(config.get_database_url())
    
    print("🔧 Testing Celery Tasks\n")
    
    # Тест 1: Парсинг
    print("1. Testing parsing task...")
    result = await parse_specific_account.run_async(
        parse_specific_account,
        username=config.instagram_authors_list[0]
    )
    print(f"   ✅ Parsed: {result}\n")
    
    # Тест 2: Обработка (если есть посты)
    if result.get("saved", 0) > 0:
        print("2. Testing processing task...")
        # Получаем ID первого поста
        from app.models import get_session, OriginalPost, PostStatus
        from sqlalchemy import select
        
        async with get_session() as session:
            res = await session.execute(
                select(OriginalPost)
                .where(OriginalPost.status == PostStatus.FILTERED)
                .limit(1)
            )
            post = res.scalar_one_or_none()
        
        if post:
            proc_result = await process_single_post.run_async(
                process_single_post,
                post_id=post.id
            )
            print(f"   ✅ Processed: {proc_result}\n")
        else:
            print("   ⚠️  No filtered posts found\n")
    
    print("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
