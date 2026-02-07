"""
Обработчик парсинга Instagram
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.utils.logger import log
from app.services.instagram_parser import InstagramParser

router = Router()


@router.message(Command("parse"))
async def cmd_parse(message: Message):
    """Запускает парсинг Instagram"""
    try:
        await message.answer("🔍 Начинаю парсинг Instagram...")
        
        parser = InstagramParser()
        authors = ["sanyaagainst", "theivansergeev", "ivan.loginov_ai"]
        
        total_posts = 0
        for author in authors:
            posts = await parser.parse_author(author)
            total_posts += len(posts)
            log.info(f"Найдено {len(posts)} постов от @{author}")
        
        await message.answer(
            f"✅ Парсинг завершен!\n\n"
            f"📊 Найдено постов: {total_posts}\n"
            f"🔔 Проверьте новые посты на одобрение."
        )
        
    except Exception as e:
        log.error(f"Ошибка в cmd_parse: {e}")
        await message.answer(f"❌ Ошибка при парсинге: {e}")
