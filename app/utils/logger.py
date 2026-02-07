"""
Настройка логирования (loguru).
"""
import sys
from pathlib import Path

from loguru import logger


def setup_logger(
    log_file: str = "logs/bot.log",
    log_level: str = "INFO",
) -> None:
    """
    Настраивает loguru logger.

    Args:
        log_file: Путь к лог файлу
        log_level: Уровень логирования
    """
    # Создаем папку для логов
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Удаляем стандартный handler
    logger.remove()

    # Console handler с цветами
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # File handler без цветов
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="10 MB",  # Ротация при 10 МБ
        retention="7 days",  # Хранить 7 дней
        compression="zip",  # Сжатие старых логов
    )

    logger.info(f"Logger initialized. Level: {log_level}, File: {log_file}")


# Реэкспорт для совместимости: from app.utils.logger import log
log = logger


# ==================== USAGE ====================

if __name__ == "__main__":
    setup_logger()
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
