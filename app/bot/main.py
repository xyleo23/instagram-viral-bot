import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from loguru import logger

from app.config import get_config
from app.utils.logger import setup_logger
from app.models import init_db, create_tables
from app.bot.middlewares.logging_middleware import LoggingMiddleware
from app.bot.handlers import start, queue, approval, history


async def main():
    """Главная функция запуска бота."""
    # Загружаем конфигурацию
    config = get_config()
    
    # Настраиваем логирование
    setup_logger(config.LOG_FILE, config.LOG_LEVEL)
    logger.info("Starting Instagram Viral Bot...")
    
    # Инициализируем БД и создаём таблицы при первом запуске
    init_db(config.get_database_url())
    await create_tables()
    logger.info("Database initialized")
    
    # Создаем бота
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    
    # Устанавливаем команды бота
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="status", description="📊 Статус системы"),
        BotCommand(command="queue", description="📥 Очередь постов"),
        BotCommand(command="history", description="📜 История"),
    ])
    
    # Создаем dispatcher с Redis storage для FSM
    storage = RedisStorage.from_url(config.REDIS_URL)
    dp = Dispatcher(storage=storage)
    
    # Регистрируем middleware
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # Регистрируем роутеры
    dp.include_router(start.router)
    dp.include_router(queue.router)
    dp.include_router(approval.router)
    dp.include_router(history.router)
    
    logger.info("All handlers registered")
    
    # Отправляем уведомление о запуске админу
    try:
        await bot.send_message(
            config.ADMIN_CHAT_ID,
            "🤖 *Instagram Viral Bot запущен!*\n\n"
            "Используйте /start для начала работы.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Could not send startup message: {e}")
    
    # Запускаем polling
    try:
        logger.info("Bot started. Polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await storage.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
