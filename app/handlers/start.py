"""
Обработчик команды /start
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.utils.logger import log

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    try:
        await message.answer(
            "🤖 <b>Instagram Automation Bot</b>\n\n"
            "Доступные команды:\n"
            "/parse - Запустить парсинг Instagram\n"
            "/stats - Статистика\n"
            "/help - Помощь",
            parse_mode="HTML"
        )
        log.info(f"Пользователь {message.from_user.id} запустил бота")
    except Exception as e:
        log.error(f"Ошибка в cmd_start: {e}")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    try:
        await message.answer(
            "📖 <b>Помощь</b>\n\n"
            "Этот бот автоматизирует создание контента для Instagram:\n\n"
            "1. Парсит вирусные посты из Instagram\n"
            "2. Обрабатывает их через AI\n"
            "3. Генерирует карусели\n"
            "4. Отправляет на одобрение в Telegram\n\n"
            "Используйте /parse для запуска парсинга.",
            parse_mode="HTML"
        )
    except Exception as e:
        log.error(f"Ошибка в cmd_help: {e}")
