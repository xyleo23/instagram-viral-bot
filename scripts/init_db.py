import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.models import init_db, create_tables
from app.utils.logger import setup_logger


async def main():
    """Инициализирует базу данных."""
    config = get_config()
    setup_logger(config.LOG_FILE, config.LOG_LEVEL)
    
    print("Initializing database...")
    print(f"Database URL: {config.get_database_url()}")
    
    # Инициализация подключения
    init_db(config.get_database_url())
    
    # Создание таблиц
    await create_tables()
    
    print("Database initialized successfully!")
    print("\nCreated tables:")
    print("  - original_posts")
    print("  - processed_posts")
    print("  - approval_history")


if __name__ == "__main__":
    asyncio.run(main())
