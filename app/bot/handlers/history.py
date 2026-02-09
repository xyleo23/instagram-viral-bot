from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from loguru import logger

from app.config import get_config
from app.bot.keyboards.inline_keyboards import get_main_menu
from app.models import (
    get_session,
    ProcessedPost,
    ProcessedStatus,
    ApprovalHistory,
)
from sqlalchemy import select, desc

router = Router(name="history")
config = get_config()

HISTORY_LIMIT = 10


@router.message(Command("history"))
async def cmd_history(message: Message):
    """
    Показывает историю обработанных постов.
    """
    if message.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    await message.answer("⏳ Загружаю историю...")
    
    try:
        async with get_session() as session:
            # Получаем последние одобренные/отклоненные посты
            result = await session.execute(
                select(ProcessedPost)
                .where(
                    ProcessedPost.status.in_([
                        ProcessedStatus.APPROVED,
                        ProcessedStatus.REJECTED,
                        ProcessedStatus.POSTED,
                    ])
                )
                .order_by(desc(ProcessedPost.updated_at))
                .limit(HISTORY_LIMIT)
            )
            posts = result.scalars().all()
            
            if not posts:
                await message.answer(
                    "📜 *История пуста*\n\nНет обработанных постов.",
                    parse_mode="Markdown"
                )
                return
            
            # Формируем текст
            text = f"📜 *История постов*\n\n"
            text += f"Последние {len(posts)} постов:\n\n"
            
            for i, post in enumerate(posts, start=1):
                # Определяем иконку статуса
                if post.status == ProcessedStatus.APPROVED:
                    status_icon = "✅"
                elif post.status == ProcessedStatus.REJECTED:
                    status_icon = "❌"
                elif post.status == ProcessedStatus.POSTED:
                    status_icon = "📤"
                else:
                    status_icon = "❓"
                
                text += f"{status_icon} *{i}. {post.title[:40]}...*\n"
                text += f"   Автор: @{post.original_post.author}\n"
                text += f"   Лайки: {post.original_post.likes:,}\n"
                text += f"   Статус: {post.status.value}\n"
                text += f"   Дата: {post.updated_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(text, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Error showing history: {e}")
        await message.answer("❌ Ошибка при получении истории")


@router.callback_query(F.data == "show_history")
async def callback_show_history(callback: CallbackQuery):
    """Callback для кнопки истории."""
    await callback.answer()
    
    # Проверка админа
    if callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    try:
        async with get_session() as session:
            # Получаем последние одобренные/отклоненные посты
            result = await session.execute(
                select(ProcessedPost)
                .where(
                    ProcessedPost.status.in_([
                        ProcessedStatus.APPROVED,
                        ProcessedStatus.REJECTED,
                        ProcessedStatus.POSTED,
                    ])
                )
                .order_by(desc(ProcessedPost.updated_at))
                .limit(HISTORY_LIMIT)
            )
            posts = result.scalars().all()
            
            if not posts:
                await callback.message.edit_text(
                    "📜 *История пуста*\n\nНет обработанных постов.",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )
                return
            
            # Формируем текст
            text = f"📜 *История постов*\n\n"
            text += f"Последние {len(posts)} постов:\n\n"
            
            for i, post in enumerate(posts, start=1):
                # Определяем иконку статуса
                if post.status == ProcessedStatus.APPROVED:
                    status_icon = "✅"
                elif post.status == ProcessedStatus.REJECTED:
                    status_icon = "❌"
                elif post.status == ProcessedStatus.POSTED:
                    status_icon = "📤"
                else:
                    status_icon = "❓"
                
                text += f"{status_icon} *{i}. {post.title[:40]}...*\n"
                text += f"   Автор: @{post.original_post.author}\n"
                text += f"   Лайки: {post.original_post.likes:,}\n"
                text += f"   Статус: {post.status.value}\n"
                text += f"   Дата: {post.updated_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await callback.message.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            
    except Exception as e:
        logger.error(f"Error showing history: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении истории",
            reply_markup=get_main_menu()
        )
