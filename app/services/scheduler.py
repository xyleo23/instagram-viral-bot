"""
Настройка расписания задач
"""
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
from app.utils.logger import log


def setup_scheduler(scheduler, bot):
    """Настраивает расписание задач"""
    
    @scheduler.scheduled_job(
        CronTrigger(hour=f"*/{settings.PARSING_INTERVAL_HOURS}"),
        id="parse_instagram"
    )
    async def scheduled_parsing():
        """Автоматический парсинг Instagram"""
        try:
            log.info("🔄 Запуск автоматического парсинга...")
            # TODO: Реализовать автоматический парсинг
            # from app.services.instagram_parser import InstagramParser
            # parser = InstagramParser()
            # await parser.parse_all_authors()
        except Exception as e:
            log.error(f"Ошибка в scheduled_parsing: {e}")
    
    @scheduler.scheduled_job(
        CronTrigger(hour="9,13,19", day_of_week="mon-fri"),
        id="post_weekdays"
    )
    async def scheduled_posting_weekdays():
        """Публикация в будни (9:00, 13:00, 19:00)"""
        try:
            log.info("📅 Запуск публикации постов (будни)...")
            # TODO: Реализовать публикацию одобренных постов
        except Exception as e:
            log.error(f"Ошибка в scheduled_posting_weekdays: {e}")
    
    @scheduler.scheduled_job(
        CronTrigger(hour=14, day_of_week=5),  # Суббота 14:00
        id="post_saturday"
    )
    async def scheduled_posting_saturday():
        """Публикация в субботу (14:00)"""
        try:
            log.info("📅 Запуск публикации постов (суббота)...")
            # TODO: Реализовать публикацию одобренных постов
        except Exception as e:
            log.error(f"Ошибка в scheduled_posting_saturday: {e}")
    
    log.info("✅ Расписание задач настроено")
