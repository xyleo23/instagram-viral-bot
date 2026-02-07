"""
Конфигурация Celery для Instagram Viral Bot.
"""
from celery import Celery
from celery.schedules import crontab
from kombu import Queue
from loguru import logger

from app.config import get_config

# Загружаем конфигурацию
config = get_config()

# Создаем Celery приложение
celery_app = Celery(
    "instagram_viral_bot",
    broker=config.celery_broker,
    backend=config.celery_backend,
    include=[
        "app.workers.tasks.parsing",
        "app.workers.tasks.processing",
        "app.workers.tasks.posting"
    ]
)

# Конфигурация
celery_app.conf.update(
    # Основные настройки
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Очереди
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("parsing", routing_key="parsing"),
        Queue("processing", routing_key="processing"),
        Queue("posting", routing_key="posting"),
    ),
    
    # Роутинг задач
    task_routes={
        "app.workers.tasks.parsing.*": {"queue": "parsing"},
        "app.workers.tasks.processing.*": {"queue": "processing"},
        "app.workers.tasks.posting.*": {"queue": "posting"},
    },
    
    # Retry настройки
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Лимиты
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    
    # Результаты
    result_expires=3600,  # 1 час
    result_backend_transport_options={"master_name": "mymaster"},
    
    # Beat schedule (cron задачи)
    beat_schedule={
        "parse-instagram-every-6-hours": {
            "task": "app.workers.tasks.parsing.parse_instagram_accounts",
            "schedule": crontab(hour="*/6"),  # Каждые 6 часов
            "options": {"queue": "parsing"}
        },
        "process-pending-posts-every-hour": {
            "task": "app.workers.tasks.processing.process_pending_posts",
            "schedule": crontab(minute=0),  # Каждый час
            "options": {"queue": "processing"}
        },
    },
)

logger.info("Celery app configured")
