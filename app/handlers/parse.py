"""
Обработчик парсинга Instagram
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import get_config
from app.models import init_db, PostStatus
from app.utils.logger import log
from app.services.instagram_parser import InstagramParser
from app.services.author_manager import AuthorManager

router = Router()


@router.message(Command("parse"))
async def cmd_parse(message: Message) -> None:
    """Запускает парсинг Instagram для указанного аккаунта."""
    text = (message.text or "").strip()
    parts = text.split(maxsplit=1)
    username = (parts[1].strip().replace("@", "") if len(parts) > 1 else "").strip()

    if not username:
        await message.answer(
            "❌ Укажите username аккаунта.\n\nПример: /parse username"
        )
        return

    config = get_config()
    init_db(config.get_database_url())
    parser = InstagramParser(settings=config)

    try:
        await message.answer(f"🔍 Парсинг аккаунта @{username}...")

        author = await AuthorManager.get_author(username)
        min_likes = author.min_likes if author else config.MIN_LIKES
        max_age_days = author.max_post_age_days if author else config.MAX_POST_AGE_DAYS

        posts = await parser.parse_accounts(
            accounts=[username],
            min_likes=min_likes,
            max_age_days=max_age_days,
            posts_limit=50,
        )

        saved = await parser.save_to_db(posts, status=PostStatus.FILTERED)

        # Триггер обработки новых постов (как в Celery-задаче)
        if saved:
            from app.workers.tasks.processing import process_single_post
            for post in saved:
                process_single_post.apply_async(args=[post.id], countdown=10)

        await message.answer(
            f"✅ Для автора @{username} найдено {len(posts)} постов, "
            f"добавлено в очередь/БД: {len(saved)}."
        )
        log.info(f"parse @{username}: found {len(posts)} posts, saved {len(saved)}")

    except Exception as e:
        log.exception(f"Ошибка в cmd_parse для @{username}: {e}")
        await message.answer(
            f"❌ Ошибка при парсинге: {e!s}\n\nПроверьте username и настройки ScrapeCreators API."
        )
    finally:
        await parser.close()
