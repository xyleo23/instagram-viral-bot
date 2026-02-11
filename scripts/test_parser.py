"""
Тестовый скрипт для Instagram парсера.
"""
import asyncio
from app.config import get_config
from app.services.instagram_parser import InstagramParser
from app.utils.logger import setup_logger
from app.models import init_db


async def main():
    """Тестирует Instagram парсер."""
    config = get_config()
    setup_logger(config.LOG_FILE, "DEBUG")
    
    # Инициализация БД
    init_db(config.get_database_url())
    
    print("🔍 Testing Instagram Parser")
    print(f"📋 Authors: {config.instagram_authors_list}")
    print(f"❤️  Min likes: {config.MIN_LIKES}")
    print(f"📅 Max age: {config.MAX_POST_AGE_DAYS} days\n")
    
    parser = InstagramParser(settings=config)
    
    try:
        # Парсим первых 2 авторов для теста
        test_authors = config.instagram_authors_list[:2]
        
        posts = await parser.parse_accounts(
            accounts=test_authors,
            min_likes=config.MIN_LIKES,
            max_age_days=config.MAX_POST_AGE_DAYS,
            posts_limit=5
        )
        
        print(f"\n✅ Parsing completed!")
        print(f"📊 Found {len(posts)} viral posts\n")
        
        if posts:
            # Сохраняем
            saved = await parser.save_to_db(posts)
            
            print(f"💾 Saved {len(saved)} posts to database\n")
            print("=" * 60)
            
            for i, post in enumerate(saved, 1):
                print(f"\n{i}. @{post.author} ({post.likes:,} likes)")
                print(f"   URL: {post.post_url}")
                print(f"   Text: {post.text[:150]}...")
                print(f"   Posted: {post.posted_at.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("⚠️  No viral posts found")
    
    finally:
        await parser.close()


if __name__ == "__main__":
    asyncio.run(main())
