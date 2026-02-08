"""
Celery задачи для парсинга Instagram.
"""
import asyncio
from typing import List, Dict
from celery import Task
from loguru import logger

from app.workers.celery_app import celery_app
from app.config import get_config
from app.models import init_db, get_session, OriginalPost, PostStatus
from app.services.instagram_parser import InstagramParser
from sqlalchemy import select


class AsyncTask(Task):
    """Базовый класс для async задач Celery."""
    
    def __call__(self, *args, **kwargs):
        """Запускает async функцию (run) в event loop."""
        result = self.run(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result


@celery_app.task(
    base=AsyncTask,
    bind=True,
    name="app.workers.tasks.parsing.parse_instagram_accounts",
    max_retries=3,
    default_retry_delay=300  # 5 минут
)
async def parse_instagram_accounts(self) -> Dict:
    """
    Парсит Instagram аккаунты и сохраняет вирусные посты.
    
    Returns:
        dict: Статистика парсинга
    """
    logger.info("Starting Instagram parsing task")
    
    config = get_config()
    init_db(config.get_database_url())
    
    parser = InstagramParser(api_key=config.APIFY_API_KEY)
    
    try:
        # 1. Парсим аккаунты
        posts = await parser.parse_accounts(
            accounts=config.instagram_authors_list,
            min_likes=config.MIN_LIKES,
            max_age_days=config.MAX_POST_AGE_DAYS,
            posts_limit=10
        )
        
        logger.info(f"Fetched {len(posts)} viral posts")
        
        # 2. Сохраняем в БД
        saved = await parser.save_to_db(posts, status=PostStatus.FILTERED)
        
        # 3. Триггерим обработку для новых постов
        from app.workers.tasks.processing import process_single_post
        
        for post in saved:
            process_single_post.apply_async(
                args=[post.id],
                countdown=10  # Запускаем через 10 секунд
            )
        
        result = {
            "status": "success",
            "fetched": len(posts),
            "saved": len(saved),
            "triggered_processing": len(saved)
        }
        
        logger.info(f"Parsing completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in parsing task: {e}")
        
        # Retry с экспоненциальным backoff
        raise self.retry(exc=e)
        
    finally:
        await parser.close()


@celery_app.task(
    base=AsyncTask,
    bind=True,
    name="app.workers.tasks.parsing.parse_specific_account",
    max_retries=2
)
async def parse_specific_account(self, username: str) -> Dict:
    """
    Парсит конкретный аккаунт Instagram.
    
    Args:
        username: Instagram username
    
    Returns:
        dict: Результат парсинга
    """
    logger.info(f"Parsing account @{username}")
    
    config = get_config()
    init_db(config.get_database_url())
    
    parser = InstagramParser(api_key=config.APIFY_API_KEY)
    
    try:
        posts = await parser.parse_accounts(
            accounts=[username],
            min_likes=config.MIN_LIKES,
            max_age_days=config.MAX_POST_AGE_DAYS,
            posts_limit=5
        )
        
        saved = await parser.save_to_db(posts)
        
        # Триггерим обработку
        from app.workers.tasks.processing import process_single_post
        
        for post in saved:
            process_single_post.apply_async(args=[post.id])
        
        return {
            "username": username,
            "fetched": len(posts),
            "saved": len(saved)
        }
        
    except Exception as e:
        logger.error(f"Error parsing @{username}: {e}")
        raise self.retry(exc=e)
        
    finally:
        await parser.close()
