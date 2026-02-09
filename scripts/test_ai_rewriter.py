"""
Тестовый скрипт для AI Rewriter.
"""
import asyncio
from app.config import get_config
from app.services.ai_rewriter import AIRewriter
from app.utils.logger import setup_logger
from app.models import init_db, get_session, OriginalPost
from sqlalchemy import select


async def main():
    """Тестирует AI Rewriter на реальных постах из БД."""
    config = get_config()
    setup_logger(config.LOG_FILE, "DEBUG")
    
    print("🤖 Testing AI Rewriter\n")
    print(f"Model: {config.OPENROUTER_MODEL}")
    print(f"Temperature: 0.85\n")
    
    # Инициализация БД
    init_db(config.get_database_url())
    
    # Получаем пост из БД
    post = None
    async with get_session() as session:
        result = await session.execute(
            select(OriginalPost)
            .where(OriginalPost.status == "filtered")
            .limit(1)
        )
        post = result.scalar_one_or_none()
    
    if not post:
        print("⚠️  No posts found in database")
        print("Run 'python scripts/test_parser.py' first")
        print("\nUsing fallback test post instead...\n")
        
        # Используем тестовый пост
        post_text = """
        Сегодня я хочу поделиться с вами своим опытом запуска успешного онлайн-бизнеса.
        
        Главное что я понял за 5 лет: успех это не про идеи, а про исполнение.
        
        У меня было 10 идей которые провалились, и только одна выстрелила.
        
        Но эта одна идея изменила всю мою жизнь. Сейчас мой доход 500к+ в месяц.
        
        Ключ к успеху: начать делать, получать обратную связь, улучшать продукт.
        
        Не ждите идеального момента. Он никогда не наступит.
        
        Начните с малого. Тестируйте гипотезы. Слушайте клиентов.
        
        Это работает. Проверено на себе.
        """
        post_author = "testauthor"
        post_likes = 10000
    else:
        post_text = post.text
        post_author = post.author
        post_likes = post.likes
        
        print(f"📄 Original Post:")
        print(f"   Author: @{post_author}")
        print(f"   Likes: {post_likes:,}")
        print(f"   Text: {post_text[:200]}...\n")
    
    # AI Rewrite
    rewriter = AIRewriter(
        api_key=config.OPENROUTER_API_KEY,
        model=config.OPENROUTER_MODEL
    )
    
    try:
        print("⏳ Rewriting with AI...")
        
        result = await rewriter.rewrite(
            text=post_text,
            author=post_author,
            slides_count=8
        )
        
        print("\n✅ AI Rewrite completed!\n")
        print("=" * 70)
        print(f"\n📝 NEW TITLE:\n{result['title']}\n")
        print(f"📊 SLIDES ({len(result['slides'])}):")
        for i, slide in enumerate(result['slides'], 1):
            print(f"\n{i}. {slide}")
        
        print(f"\n💬 CAPTION:\n{result['caption']}\n")
        print(f"🏷️  HASHTAGS:\n{result['hashtags']}\n")
        print("=" * 70)
        print(f"\n💰 Cost: ${result['cost_usd']:.4f}")
        print(f"🔢 Tokens: {result['tokens_used']}")
        print(f"🤖 Model: {result['ai_model']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure OPENROUTER_API_KEY is set in .env file")
        
    finally:
        await rewriter.close()


if __name__ == "__main__":
    asyncio.run(main())
