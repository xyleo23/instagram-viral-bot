"""
Celery задачи для AI обработки постов.
"""
import asyncio
from typing import Dict, Optional
from celery import Task
from loguru import logger

from app.workers.celery_app import celery_app
from app.config import get_config
from app.models import (
    init_db, get_session, 
    OriginalPost, ProcessedPost, PostStatus, ProcessedStatus
)
from app.services.ai_rewriter import AIRewriter
from app.services.carousel_generator import CarouselGenerator
from app.services.yandex_disk import YandexDiskUploader
from sqlalchemy import select


class AsyncTask(Task):
    """Базовый класс для async задач Celery."""
    
    def __call__(self, *args, **kwargs):
        result = self.run(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result


@celery_app.task(
    base=AsyncTask,
    bind=True,
    name="app.workers.tasks.processing.process_pending_posts",
    max_retries=2
)
async def process_pending_posts(self) -> Dict:
    """
    Обрабатывает все посты со статусом FILTERED.
    
    Returns:
        dict: Статистика обработки
    """
    logger.info("Processing pending posts task started")
    
    config = get_config()
    init_db(config.get_database_url())
    
    # Получаем посты для обработки
    async for session in get_session():
        result = await session.execute(
            select(OriginalPost)
            .where(OriginalPost.status == PostStatus.FILTERED)
            .limit(5)  # Обрабатываем по 5 за раз
        )
        posts = result.scalars().all()
    
    if not posts:
        logger.info("No pending posts to process")
        return {"status": "success", "processed": 0}
    
    logger.info(f"Found {len(posts)} posts to process")
    
    # Обрабатываем каждый пост
    processed_count = 0
    for post in posts:
        try:
            # Запускаем задачу обработки
            process_single_post.apply_async(
                args=[post.id],
                countdown=5  # Задержка между постами
            )
            processed_count += 1
        except Exception as e:
            logger.error(f"Error queuing post {post.id}: {e}")
    
    return {
        "status": "success",
        "found": len(posts),
        "queued": processed_count
    }


@celery_app.task(
    base=AsyncTask,
    bind=True,
    name="app.workers.tasks.processing.process_single_post",
    max_retries=3,
    default_retry_delay=600  # 10 минут
)
async def process_single_post(self, post_id: int) -> Dict:
    """
    Обрабатывает один пост: AI рерайт + генерация изображений + загрузка.
    
    Args:
        post_id: ID оригинального поста
    
    Returns:
        dict: Результат обработки
    """
    logger.info(f"Processing post {post_id}")
    
    config = get_config()
    init_db(config.get_database_url())
    
    # 1. Получаем пост из БД
    async for session in get_session():
        result = await session.execute(
            select(OriginalPost).where(OriginalPost.id == post_id)
        )
        post = result.scalar_one_or_none()
    
    if not post:
        logger.error(f"Post {post_id} not found")
        return {"status": "error", "message": "Post not found"}
    
    if post.status != PostStatus.FILTERED:
        logger.warning(f"Post {post_id} already processed (status: {post.status})")
        return {"status": "skipped", "reason": "Already processed"}
    
    # Обновляем статус
    async for session in get_session():
        post.status = PostStatus.PROCESSING
        session.add(post)
        await session.commit()
    
    logger.info(f"Processing: @{post.author}, {post.likes} likes")
    
    try:
        # 2. AI Rewrite
        logger.info("Step 1/3: AI rewriting...")
        rewriter = AIRewriter(
            api_key=config.OPENROUTER_API_KEY,
            model=config.OPENROUTER_MODEL
        )
        
        ai_result = await rewriter.rewrite(
            text=post.text,
            author=post.author,
            slides_count=8
        )
        await rewriter.close()
        
        logger.info(f"AI rewrite done: {ai_result['tokens_used']} tokens, ${ai_result['cost_usd']:.4f}")
        
        # 3. Generate carousel images
        logger.info("Step 2/3: Generating carousel images...")
        generator = CarouselGenerator(use_local=True)
        
        images = await generator.generate(
            slides=ai_result["slides"],
            width=1080,
            height=1080
        )
        await generator.close()
        
        logger.info(f"Generated {len(images)} images")
        
        # 4. Upload to Yandex.Disk
        logger.info("Step 3/3: Uploading to Yandex.Disk...")
        uploader = YandexDiskUploader(token=config.YANDEX_DISK_TOKEN)
        
        upload_result = await uploader.upload_images(
            images=images,
            post_id=post.id
        )
        await uploader.close()
        
        logger.info(f"Uploaded to: {upload_result['folder_url']}")
        
        # 5. Сохраняем ProcessedPost в БД
        async for session in get_session():
            processed_post = ProcessedPost(
                original_post_id=post.id,
                title=ai_result["title"],
                caption=ai_result["caption"],
                hashtags=ai_result["hashtags"],
                slides=ai_result["slides"],
                slides_count=len(ai_result["slides"]),
                ai_model=ai_result["ai_model"],
                tokens_used=ai_result["tokens_used"],
                cost_usd=ai_result["cost_usd"],
                image_urls=images,  # Base64 или URLs
                yandex_disk_folder=upload_result["folder_url"],
                status=ProcessedStatus.PENDING_APPROVAL
            )
            
            session.add(processed_post)
            
            # Обновляем статус оригинального поста
            post.status = PostStatus.PROCESSED
            session.add(post)
            
            await session.commit()
            await session.refresh(processed_post)
        
        logger.info(f"Post {post_id} processed successfully -> ProcessedPost {processed_post.id}")
        
        # 6. Отправляем уведомление в Telegram
        from aiogram import Bot
        from app.bot.handlers.approval import send_post_for_approval
        
        bot = Bot(token=config.BOT_TOKEN)
        try:
            await send_post_for_approval(bot, processed_post.id)
            logger.info(f"Approval notification sent for post {processed_post.id}")
        except Exception as e:
            logger.error(f"Error sending approval notification: {e}")
        finally:
            await bot.session.close()
        
        return {
            "status": "success",
            "post_id": post.id,
            "processed_post_id": processed_post.id,
            "cost_usd": ai_result["cost_usd"],
            "yandex_url": upload_result["folder_url"]
        }
        
    except Exception as e:
        logger.error(f"Error processing post {post_id}: {e}")
        
        # Откатываем статус
        async for session in get_session():
            post.status = PostStatus.FILTERED
            session.add(post)
            await session.commit()
        
        # Retry
        raise self.retry(exc=e)
