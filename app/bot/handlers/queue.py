from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from loguru import logger
from sqlalchemy import select, func

from app.config import get_config
from app.models import (
    get_session,
    ProcessedPost,
    OriginalPost,
    ProcessedStatus,
    ApprovalHistory,
    DecisionType,
)
from app.bot.keyboards.inline_keyboards import get_main_menu
from app.bot.keyboards.inline import get_queue_post_keyboard
from datetime import datetime

router = Router(name="queue")
config = get_config()

POSTS_PER_PAGE = 1  # Показываем по 1 посту с полным превью и кнопками


def _escape_markdown(text: str) -> str:
    """Экранирует спецсимволы для Markdown parse_mode (_ * ` [ ])."""
    if not text:
        return ""
    for ch in "_*`[]":
        text = text.replace(ch, f"\\{ch}")
    return text


async def show_queue_page(message: Message, page: int = 0, edit: bool = False):
    """
    Показывает страницу очереди постов с полным превью и кнопками.
    
    Args:
        message: Сообщение для ответа
        page: Номер страницы (начиная с 0)
        edit: Редактировать существующее сообщение или отправить новое
    """
    try:
        async for session in get_session():
            # Общее количество постов
            count_result = await session.execute(
                select(func.count(ProcessedPost.id)).where(
                    ProcessedPost.status == ProcessedStatus.PENDING_APPROVAL
                )
            )
            total_posts = count_result.scalar() or 0

            if total_posts == 0:
                text = "📋 *Очередь пуста*\n\nНет постов, ожидающих одобрения."
                if edit:
                    await message.edit_text(
                        text,
                        parse_mode="Markdown",
                        reply_markup=get_main_menu(),
                    )
                else:
                    await message.answer(
                        text,
                        parse_mode="Markdown",
                        reply_markup=get_main_menu(),
                    )
                return

            total_pages = max(1, (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE)
            page = max(0, min(page, total_pages - 1))

            # JOIN для получения ProcessedPost + OriginalPost без lazy load
            result = await session.execute(
                select(ProcessedPost, OriginalPost)
                .join(
                    OriginalPost,
                    ProcessedPost.original_post_id == OriginalPost.id,
                )
                .where(
                    ProcessedPost.status == ProcessedStatus.PENDING_APPROVAL,
                )
                .order_by(ProcessedPost.created_at.desc())
                .limit(POSTS_PER_PAGE)
                .offset(page * POSTS_PER_PAGE)
            )
            rows = result.all()

            if not rows:
                text = "📋 *Очередь пуста*\n\nНет постов на этой странице."
                if edit:
                    await message.edit_text(
                        text,
                        parse_mode="Markdown",
                        reply_markup=get_main_menu(),
                    )
                else:
                    await message.answer(
                        text,
                        parse_mode="Markdown",
                        reply_markup=get_main_menu(),
                    )
                return

            # Берём первый пост (при POSTS_PER_PAGE=1)
            post, original = rows[0]
            post_idx = page * POSTS_PER_PAGE + 1

            # Извлекаем данные в переменные (до выхода из сессии)
            title = _escape_markdown(post.title or "")
            raw_caption = (post.caption or "")[:200]
            if len(post.caption or "") > 200:
                raw_caption += "..."
            caption = _escape_markdown(raw_caption)
            slides_count = post.slides_count or len(post.slides or [])
            hashtags = _escape_markdown(post.hashtags or "")
            author = _escape_markdown(original.author or "?")
            likes = original.likes or 0

            likes_str = f"{likes:,}" if likes else "0"
            text = (
                "📋 *Очередь на одобрение*\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"📌 *Пост #{post_idx}*\n\n"
                f"📝 *Заголовок:*\n{title}\n\n"
                f"📄 *Текст:*\n{caption}\n\n"
                f"📊 *Слайдов:* {slides_count}\n"
                f"🏷 *Хэштеги:* {hashtags}\n\n"
                f"👤 *Источник:* @{author} ({likes_str} лайков)\n"
                "━━━━━━━━━━━━━━━━━━\n"
            )

            keyboard = get_queue_post_keyboard(
                post_id=post.id,
                page=page,
                total_pages=total_pages,
            )

            if edit:
                await message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            else:
                await message.answer(
                    text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )

    except Exception as e:
        logger.error(f"Error showing queue: {e}", exc_info=True)
        error_text = "❌ Ошибка при получении очереди"
        try:
            if edit:
                await message.edit_text(
                    error_text,
                    reply_markup=get_main_menu(),
                )
            else:
                await message.answer(
                    error_text,
                    reply_markup=get_main_menu(),
                )
        except Exception as inner:
            logger.error(f"Error sending error message: {inner}", exc_info=True)


# ==================== COMMAND & CALLBACK HANDLERS ====================


@router.message(Command("queue"))
async def cmd_queue(message: Message):
    """Показывает очередь постов на одобрение."""
    if message.from_user and message.from_user.id != config.ADMIN_CHAT_ID:
        return
    await show_queue_page(message, page=0)


@router.callback_query(F.data == "show_queue")
async def callback_show_queue(callback: CallbackQuery):
    """Callback для кнопки очереди."""
    await callback.answer()
    if callback.message:
        await show_queue_page(callback.message, page=0)


@router.callback_query(F.data.startswith("queue_page:"))
async def callback_queue_page(callback: CallbackQuery):
    """Навигация по страницам очереди."""
    try:
        page = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        page = 0
    await callback.answer()
    if callback.message:
        await show_queue_page(callback.message, page=page, edit=True)


@router.callback_query(F.data == "queue_noop")
async def callback_queue_noop(callback: CallbackQuery):
    """Заглушка для кнопки с номером страницы."""
    await callback.answer()


# ==================== APPROVE / REJECT / VIEW HANDLERS ====================


@router.callback_query(F.data.startswith("approve_"))
async def callback_approve_post(callback: CallbackQuery):
    """Обрабатывает нажатие 'Одобрить' из очереди."""
    await callback.answer("✅ Пост одобрен!")
    try:
        post_id = int(callback.data.replace("approve_", ""))
    except (ValueError, AttributeError):
        logger.error(f"Invalid approve callback data: {callback.data}")
        return

    logger.info(f"User {callback.from_user.id} approving post {post_id} from queue")

    try:
        async for session in get_session():
            result = await session.execute(
                select(ProcessedPost).where(ProcessedPost.id == post_id)
            )
            post = result.scalar_one_or_none()

            if not post:
                if callback.message:
                    await callback.message.edit_text(
                        "❌ Пост не найден",
                        reply_markup=get_main_menu(),
                    )
                return

            post.status = ProcessedStatus.APPROVED
            session.add(post)
            approval = ApprovalHistory(
                processed_post_id=post_id,
                user_id=callback.from_user.id if callback.from_user else 0,
                username=callback.from_user.username if callback.from_user else None,
                decision=DecisionType.APPROVED,
                comment=None,
                timestamp=datetime.utcnow(),
            )
            session.add(approval)

        if callback.message:
            await show_queue_page(callback.message, page=0, edit=True)

    except Exception as e:
        logger.error(f"Error approving post {post_id}: {e}", exc_info=True)
        if callback.message:
            await callback.message.answer(
                "❌ Ошибка при одобрении поста",
                reply_markup=get_main_menu(),
            )


@router.callback_query(F.data.startswith("reject_"))
async def callback_reject_post(callback: CallbackQuery):
    """Обрабатывает нажатие 'Отклонить' из очереди."""
    await callback.answer("❌ Пост отклонён")
    try:
        post_id = int(callback.data.replace("reject_", ""))
    except (ValueError, AttributeError):
        logger.error(f"Invalid reject callback data: {callback.data}")
        return

    logger.info(f"User {callback.from_user.id} rejecting post {post_id} from queue")

    try:
        async for session in get_session():
            result = await session.execute(
                select(ProcessedPost).where(ProcessedPost.id == post_id)
            )
            post = result.scalar_one_or_none()

            if not post:
                if callback.message:
                    await callback.message.edit_text(
                        "❌ Пост не найден",
                        reply_markup=get_main_menu(),
                    )
                return

            post.status = ProcessedStatus.REJECTED
            session.add(post)
            approval = ApprovalHistory(
                processed_post_id=post_id,
                user_id=callback.from_user.id if callback.from_user else 0,
                username=callback.from_user.username if callback.from_user else None,
                decision=DecisionType.REJECTED,
                comment=None,
                timestamp=datetime.utcnow(),
            )
            session.add(approval)

        if callback.message:
            await show_queue_page(callback.message, page=0, edit=True)

    except Exception as e:
        logger.error(f"Error rejecting post {post_id}: {e}", exc_info=True)
        if callback.message:
            await callback.message.answer(
                "❌ Ошибка при отклонении поста",
                reply_markup=get_main_menu(),
            )


@router.callback_query(F.data.startswith("view_"))
async def callback_view_post(callback: CallbackQuery):
    """Показывает полную информацию о посте со всеми слайдами."""
    await callback.answer()
    try:
        post_id = int(callback.data.replace("view_", ""))
    except (ValueError, AttributeError):
        logger.error(f"Invalid view callback data: {callback.data}")
        return

    try:
        async for session in get_session():
            result = await session.execute(
                select(ProcessedPost, OriginalPost)
                .join(
                    OriginalPost,
                    ProcessedPost.original_post_id == OriginalPost.id,
                )
                .where(ProcessedPost.id == post_id)
            )
            row = result.first()
            if not row:
                if callback.message:
                    await callback.message.answer(
                        "❌ Пост не найден",
                        reply_markup=get_main_menu(),
                    )
                return

            post, original = row
            slides = post.slides or []
            slides_text = "\n\n".join(
                f"*Слайд {i + 1}:*\n{_escape_markdown(str(s)[:300])}{'...' if len(str(s)) > 300 else ''}"
                for i, s in enumerate(slides)
            )
            likes_str = f"{original.likes:,}" if original.likes else "0"
            text = (
                "📋 *Полный просмотр поста*\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"📝 *Заголовок:*\n{_escape_markdown(post.title or '')}\n\n"
                f"📄 *Текст:*\n{_escape_markdown(post.caption or '')}\n\n"
                f"🏷 *Хэштеги:*\n{_escape_markdown(post.hashtags or '')}\n\n"
                f"📊 *Слайдов:* {post.slides_count}\n\n"
                "📑 *Слайды:*\n\n"
                f"{slides_text or 'Нет слайдов'}\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Источник:* @{_escape_markdown(original.author or '?')} ({likes_str} лайков)"
            )

            if callback.message:
                await callback.message.answer(
                    text,
                    parse_mode="Markdown",
                    reply_markup=get_main_menu(),
                )

    except Exception as e:
        logger.error(f"Error viewing post {post_id}: {e}", exc_info=True)
        if callback.message:
            await callback.message.answer(
                "❌ Ошибка при загрузке поста",
                reply_markup=get_main_menu(),
            )


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Возврат в главное меню."""
    await callback.answer()
    if not callback.message:
        return
    text = (
        "🎉 *Главное меню*\n\n"
        "Выберите действие:"
    )
    try:
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
    except Exception as e:
        logger.error(f"Error showing main menu: {e}", exc_info=True)
