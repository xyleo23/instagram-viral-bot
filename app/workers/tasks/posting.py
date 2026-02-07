"""
Celery задачи для постинга в Instagram (placeholder).
"""
import asyncio
from typing import Dict
from celery import Task
from loguru import logger

from app.workers.celery_app import celery_app


class AsyncTask(Task):
    """Базовый класс для async задач."""
    
    def __call__(self, *args, **kwargs):
        return asyncio.run(self.run_async(*args, **kwargs))
    
    async def run_async(self, *args, **kwargs):
        raise NotImplementedError


@celery_app.task(
    base=AsyncTask,
    bind=True,
    name="app.workers.tasks.posting.post_to_instagram",
    max_retries=3
)
async def post_to_instagram(self, processed_post_id: int) -> Dict:
    """
    Публикует пост в Instagram.
    
    Args:
        processed_post_id: ID обработанного поста
    
    Returns:
        dict: Результат публикации
    """
    logger.info(f"Posting ProcessedPost {processed_post_id} to Instagram")
    
    # TODO: Реализовать постинг через Instagram Graph API
    # или instagrapi
    
    logger.warning("Instagram posting not implemented yet")
    
    return {
        "status": "not_implemented",
        "processed_post_id": processed_post_id
    }
