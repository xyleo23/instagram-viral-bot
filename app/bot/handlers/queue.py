from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.config import get_config
from app.models import get_session, ProcessedPost, ProcessedStatus
from app.bot.keyboards.inline_keyboards import get_main_menu, get_queue_keyboard_with_menu

router = Router(name="queue")
config = get_config()

POSTS_PER_PAGE = 5


@router.message(Command("queue"))
async def cmd_queue(message: Message):
    """
    Показывает очередь постов на одобрение.
    """
    if message.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    await show_queue_page(message, page=0)


@router.callback_query(F.data == "show_queue")
async def callback_show_queue(callback: CallbackQuery):
    """Callback для кнопки очереди."""
    await callback.answer()
    await show_queue_page(callback.message, page=0)


@router.callback_query(F.data.startswith("queue_page:"))
async def callback_queue_page(callback: CallbackQuery):
    """Навигация по страницам очереди."""
    page = int(callback.data.split(":")[1])
    await callback.answer()
    await show_queue_page(callback.message, page=page, edit=True)


@router.callback_query(F.data == "queue_noop")
async def callback_queue_noop(callback: CallbackQuery):
    """Заглушка для кнопки с номером страницы."""
    await callback.answer()


async def show_queue_page(message: Message, page: int = 0, edit: bool = False):
    """
    Показывает страницу очереди постов.
    
    Args:
        message: Сообщение для ответа
        page: Номер страницы (начиная с 0)
        edit: Редактировать существующее сообщение или отправить новое
    """
    try:
        async for session in get_session():
            # Получаем общее количество постов (асинхронный count)
            count_result = await session.execute(
                select(func.count(ProcessedPost.id))
                .where(ProcessedPost.status == ProcessedStatus.PENDING_APPROVAL)
            )
            total_posts = count_result.scalar() or 0
            
            if total_posts == 0:
                text = "📋 *Очередь пуста*\n\nНет постов, ожидающих одобрения."
                if edit:
                    await message.edit_text(
                        text,
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )
                else:
                    await message.answer(
                        text,
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )
                return
            
            # Вычисляем пагинацию
            total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
            page = max(0, min(page, total_pages - 1))
            
            # Загружаем только нужную страницу с eager load original_post
            # (избегаем lazy load → greenlet_spawn)
            posts_result = await session.execute(
                select(ProcessedPost)
                .options(selectinload(ProcessedPost.original_post))
                .where(ProcessedPost.status == ProcessedStatus.PENDING_APPROVAL)
                .order_by(ProcessedPost.created_at.desc())
                .limit(POSTS_PER_PAGE)
                .offset(page * POSTS_PER_PAGE)
            )
            posts = posts_result.scalars().all()
            offset = page * POSTS_PER_PAGE
            
            # Формируем текст
            text = f"📋 *Очередь на одобрение*\n\n"
            text += f"Всего постов: {total_posts}\n"
            text += f"Страница {page + 1} из {total_pages}\n\n"
            
            for i, post in enumerate(posts, start=offset + 1):
                # original_post загружен через selectinload (без lazy load)
                original = post.original_post
                author = original.author if original else "?"
                likes = original.likes if original else 0
                text += f"*{i}. {post.title[:50]}...*\n"
                text += f"   Автор: @{author}\n"
                text += f"   Лайки: {likes:,}\n"
                text += f"   ID: `{post.id}`\n\n"
            
            keyboard = get_queue_keyboard_with_menu(page, total_pages)
            
            if edit:
                await message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            else:
                await message.answer(
                    text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                
    except Exception as e:
        logger.error(f"Error showing queue: {e}")
        error_text = "❌ Ошибка при получении очереди"
        if edit:
            await message.edit_text(error_text, reply_markup=get_main_menu())
        else:
            await message.answer(error_text, reply_markup=get_main_menu())
