"""
Главный файл приложения
Точка входа для запуска бота
"""
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_config, settings
from app.utils.logger import setup_logger, log
from app.handlers import start, parse, approval, carousel
from app.services.scheduler import setup_scheduler


async def main():
    """Главная функция запуска бота"""
    config = get_config()
    setup_logger(log_file=config.LOG_FILE, log_level=config.LOG_LEVEL)

    log.info("🚀 Запуск Instagram Automation Bot...")
    
    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(parse.router)
    dp.include_router(approval.router)
    dp.include_router(carousel.router)
    
    # Настройка расписания
    scheduler = AsyncIOScheduler()
    setup_scheduler(scheduler, bot)
    scheduler.start()
    
    log.info("✅ Бот запущен и готов к работе!")
    
    try:
        # Запуск polling
        await dp.start_polling(bot, skip_updates=True)
    except KeyboardInterrupt:
        log.info("⏹ Остановка бота...")
    finally:
        scheduler.shutdown()
        await bot.session.close()
        log.info("👋 Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        log.error(f"❌ Критическая ошибка: {e}")
        raise
