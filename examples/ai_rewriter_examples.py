"""
Примеры использования AI Rewriter в различных сценариях.
"""
import asyncio
from typing import List
from app.services.ai_rewriter import AIRewriter
from app.config import get_config


# ==================== ПРИМЕР 1: Базовое использование ====================

async def example_basic():
    """Базовый пример использования AI Rewriter."""
    print("\n" + "="*70)
    print("ПРИМЕР 1: Базовое использование")
    print("="*70 + "\n")
    
    config = get_config()
    rewriter = AIRewriter(
        api_key=config.OPENROUTER_API_KEY,
        model=config.OPENROUTER_MODEL
    )
    
    try:
        post_text = """
        Сегодня хочу рассказать как я заработал первый миллион на AI.
        
        Всё началось с простой идеи: автоматизировать рутинные задачи.
        
        Я создал бота который экономит 10 часов в неделю.
        
        Продал его за 500к. Потом ещё 5 таких проектов.
        
        Итого: 1M за 6 месяцев работы.
        """
        
        result = await rewriter.rewrite(
            text=post_text,
            author="@testuser",
            slides_count=8
        )
        
        print(f"✅ Заголовок: {result['title']}")
        print(f"\n📊 Слайды ({len(result['slides'])}):")
        for i, slide in enumerate(result['slides'], 1):
            print(f"  {i}. {slide}")
        
        print(f"\n💰 Стоимость: ${result['cost_usd']:.4f}")
        print(f"🔢 Токены: {result['tokens_used']}")
        
    finally:
        await rewriter.close()


# ==================== ПРИМЕР 2: Батчинг (несколько постов) ====================

async def example_batch():
    """Обработка нескольких постов параллельно."""
    print("\n" + "="*70)
    print("ПРИМЕР 2: Батчинг (параллельная обработка)")
    print("="*70 + "\n")
    
    config = get_config()
    rewriter = AIRewriter(
        api_key=config.OPENROUTER_API_KEY,
        model=config.OPENROUTER_MODEL
    )
    
    posts = [
        {
            "text": "Первый пост о бизнесе...",
            "author": "@user1"
        },
        {
            "text": "Второй пост о мотивации...",
            "author": "@user2"
        },
        {
            "text": "Третий пост о саморазвитии...",
            "author": "@user3"
        }
    ]
    
    try:
        # Создаем задачи для параллельного выполнения
        tasks = [
            rewriter.rewrite(post["text"], post["author"])
            for post in posts
        ]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks)
        
        total_cost = sum(r["cost_usd"] for r in results)
        total_tokens = sum(r["tokens_used"] for r in results)
        
        print(f"✅ Обработано постов: {len(results)}")
        print(f"💰 Общая стоимость: ${total_cost:.4f}")
        print(f"🔢 Всего токенов: {total_tokens}")
        
        for i, result in enumerate(results, 1):
            print(f"\nПост {i}: {result['title'][:50]}...")
        
    finally:
        await rewriter.close()


# ==================== ПРИМЕР 3: Разные модели ====================

async def example_models():
    """Сравнение разных AI моделей."""
    print("\n" + "="*70)
    print("ПРИМЕР 3: Сравнение моделей")
    print("="*70 + "\n")
    
    config = get_config()
    
    test_post = """
    Сегодня я понял главное: успех это не про удачу, а про систему.
    
    Я работаю по 4 часа в день и зарабатываю больше чем раньше за 12.
    
    Секрет: автоматизация и делегирование.
    """
    
    models = [
        "anthropic/claude-3.5-sonnet",
        "google/gemini-pro-1.5",
        # "openai/gpt-4-turbo",  # Дорогая модель, закомментирована
    ]
    
    for model in models:
        print(f"\n🤖 Тестируем модель: {model}")
        
        rewriter = AIRewriter(
            api_key=config.OPENROUTER_API_KEY,
            model=model
        )
        
        try:
            result = await rewriter.rewrite(
                text=test_post,
                author="@testuser",
                slides_count=6
            )
            
            print(f"  ✅ Заголовок: {result['title'][:60]}...")
            print(f"  💰 Стоимость: ${result['cost_usd']:.4f}")
            print(f"  🔢 Токены: {result['tokens_used']}")
            
        finally:
            await rewriter.close()


# ==================== ПРИМЕР 4: Обработка ошибок ====================

async def example_error_handling():
    """Обработка ошибок и fallback."""
    print("\n" + "="*70)
    print("ПРИМЕР 4: Обработка ошибок")
    print("="*70 + "\n")
    
    # Используем неправильный API ключ для демонстрации fallback
    rewriter = AIRewriter(
        api_key="invalid_key",
        model="anthropic/claude-3.5-sonnet"
    )
    
    try:
        result = await rewriter.rewrite(
            text="Тестовый пост для демонстрации fallback парсинга.",
            author="@testuser"
        )
        
        if result["ai_model"] == "fallback":
            print("⚠️  AI недоступен, использован fallback парсинг")
        else:
            print("✅ AI обработка успешна")
        
        print(f"\nЗаголовок: {result['title']}")
        print(f"Слайдов: {len(result['slides'])}")
        print(f"Модель: {result['ai_model']}")
        
    finally:
        await rewriter.close()


# ==================== ПРИМЕР 5: Интеграция с БД ====================

async def example_database_integration():
    """Пример интеграции с базой данных."""
    print("\n" + "="*70)
    print("ПРИМЕР 5: Интеграция с БД")
    print("="*70 + "\n")
    
    from app.models import get_session, OriginalPost, ProcessedPost
    from sqlalchemy import select
    
    config = get_config()
    rewriter = AIRewriter(
        api_key=config.OPENROUTER_API_KEY,
        model=config.OPENROUTER_MODEL
    )
    
    try:
        # Получаем посты из БД
        async with get_session() as session:
            result = await session.execute(
                select(OriginalPost)
                .where(OriginalPost.status == "filtered")
                .limit(3)
            )
            posts = result.scalars().all()
        
        if not posts:
            print("⚠️  Нет постов в БД")
            return
        
        print(f"📊 Найдено постов: {len(posts)}")
        
        for post in posts:
            print(f"\n🔄 Обрабатываем пост от @{post.author}...")
            
            # AI обработка
            ai_result = await rewriter.rewrite(
                text=post.text,
                author=post.author
            )
            
            # Сохраняем в БД
            async with get_session() as session:
                processed = ProcessedPost(
                    original_post_id=post.id,
                    title=ai_result["title"],
                    slides=ai_result["slides"],
                    caption=ai_result["caption"],
                    hashtags=ai_result["hashtags"],
                    ai_model=ai_result["ai_model"],
                    tokens_used=ai_result["tokens_used"],
                    cost_usd=ai_result["cost_usd"]
                )
                session.add(processed)
                await session.commit()
            
            print(f"  ✅ Сохранено: {ai_result['title'][:50]}...")
            print(f"  💰 Стоимость: ${ai_result['cost_usd']:.4f}")
        
    finally:
        await rewriter.close()


# ==================== ПРИМЕР 6: Кастомный промпт ====================

async def example_custom_prompt():
    """Пример с кастомным промптом."""
    print("\n" + "="*70)
    print("ПРИМЕР 6: Кастомный промпт")
    print("="*70 + "\n")
    
    config = get_config()
    
    # Создаем кастомный rewriter
    class CustomRewriter(AIRewriter):
        def _build_prompt(self, text, author, slides_count, style):
            """Кастомный промпт для образовательного контента."""
            return f"""Ты эксперт по образовательному контенту.

Переписать пост в формат обучающей карусели из {slides_count} слайдов.

СТРУКТУРА:
1. Проблема
2-{slides_count-1}. Решение (по шагам)
{slides_count}. Итог и призыв к действию

СТИЛЬ: Простой, понятный, с примерами.

ОТВЕТ В JSON:
{{
  "title": "...",
  "slides": ["...", "..."],
  "caption": "...",
  "hashtags": "..."
}}

ПОСТ:
{text}"""
    
    rewriter = CustomRewriter(
        api_key=config.OPENROUTER_API_KEY,
        model=config.OPENROUTER_MODEL
    )
    
    try:
        result = await rewriter.rewrite(
            text="Как научиться программировать за 3 месяца...",
            author="@eduuser"
        )
        
        print(f"✅ Заголовок: {result['title']}")
        print(f"\n📚 Образовательные слайды:")
        for i, slide in enumerate(result['slides'], 1):
            print(f"  {i}. {slide[:60]}...")
        
    finally:
        await rewriter.close()


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

async def main():
    """Запускает все примеры."""
    print("\n" + "="*70)
    print("🤖 AI REWRITER - ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ")
    print("="*70)
    
    examples = [
        ("Базовое использование", example_basic),
        ("Батчинг", example_batch),
        ("Сравнение моделей", example_models),
        ("Обработка ошибок", example_error_handling),
        ("Интеграция с БД", example_database_integration),
        ("Кастомный промпт", example_custom_prompt),
    ]
    
    print("\nДоступные примеры:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nВыберите пример (1-6) или 0 для запуска всех:")
    try:
        choice = int(input("> "))
    except (ValueError, EOFError):
        choice = 1  # По умолчанию первый пример
    
    if choice == 0:
        # Запускаем все примеры
        for name, func in examples:
            try:
                await func()
            except Exception as e:
                print(f"\n❌ Ошибка в примере '{name}': {e}")
    elif 1 <= choice <= len(examples):
        # Запускаем выбранный пример
        name, func = examples[choice - 1]
        try:
            await func()
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
    else:
        print("❌ Неверный выбор")
    
    print("\n" + "="*70)
    print("✅ Примеры завершены!")
    print("="*70 + "\n")


if __name__ == "__main__":
    from app.utils.logger import setup_logger
    setup_logger()
    
    asyncio.run(main())
