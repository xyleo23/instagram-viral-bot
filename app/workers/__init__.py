"""
Celery workers для Instagram Viral Bot.
"""
from app.workers.celery_app import celery_app
from app.workers.tasks import parsing, processing, posting

__all__ = ["celery_app", "parsing", "processing", "posting"]
