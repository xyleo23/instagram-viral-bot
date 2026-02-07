import asyncio
import base64
from io import BytesIO
from typing import List, Optional
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, 
    InputMediaPhoto, BufferedInputFile,
    FSInputFile
)
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.config import get_config
from app.models import (
    get_session, ProcessedPost, OriginalPost, 
    ApprovalHistory, ProcessedStatus, DecisionType, PostStatus
)
from app.bot.keyboards.inline import get_approval_keyboard
from app.bot.states import ApprovalStates
from sqlalchemy import select
from datetime import datetime

router = Router(name="approval")
config = get_config()


async def send_post_for_approval(
    bot: Bot,
    processed_post_id: int
) -> None:
    """
    Отправляет пост на одобрение админу в Telegram.
    
    Args:
        bot: Экземпляр бота
        processed_post_id: ID обработанного поста
    """
    logger.info(f"Sending ProcessedPost {processed_post_id} for approval")
    
    # Получаем пост из БД
    async for session in get_session():
        result = await session.execute(
            select(ProcessedPost)
            .where(ProcessedPost.id == processed_post_id)
        )
        processed_post = result.scalar_one_or_none()
        
        if not processed_post:
            logger.error(f"ProcessedPost {processed_post_id} not found")
            return
        
        # Загружаем оригинальный пост
        result = await session.execute(
            select(OriginalPost)
            .where(OriginalPost.id == processed_post.original_post_id)
        )
        original_post = result.scalar_one_or_none()
    
    if not original_post:
        logger.error(f"OriginalPost {processed_post.original_post_id} not found")
        return
    
    try:
        # 1. Подготовка изображений
        media_group = await _prepare_media_group(processed_post.image_urls)
        
        if not media_group:
            logger.warning("No images to send, sending text only")
        
        # 2. Отправка media group (если есть изображения)
        if media_group:
            await bot.send_media_group(
                chat_id=config.ADMIN_CHAT_ID,
                media=media_group
            )
            
            # Небольшая задержка перед отправкой текста
            await asyncio.sleep(0.5)
        
        # 3. Формирование текста
        text = _format_approval_message(original_post, processed_post)
        
        # 4. Клавиатура с кнопками
        keyboard = get_approval_keyboard(processed_post.id)
        
        # Добавляем ссылку на Яндекс.Диск если есть
        if processed_post.yandex_disk_folder:
            # Обновляем клавиатуру с реальной ссылкой
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            from aiogram.types import InlineKeyboardButton
            
            builder = InlineKeyboardBuilder()
            
            # Копируем существующие кнопки (все кроме последней placeholder)
            for row in keyboard.inline_keyboard[:-1]:
                builder.row(*row)
            
            # Добавляем кнопку с реальной ссылкой
            builder.row(
                InlineKeyboardButton(
                    text="🔗 Открыть на Яндекс.Диске",
                    url=processed_post.yandex_disk_folder
                )
            )
            
            keyboard = builder.as_markup()
        
        # 5. Отправка текста с кнопками
        await bot.send_message(
            chat_id=config.ADMIN_CHAT_ID,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        
        logger.info(f"Post {processed_post_id} sent for approval successfully")
        
    except Exception as e:
        logger.error(f"Error sending post for approval: {e}", exc_info=True)
        
        # Отправляем хотя бы текст
        try:
            await bot.send_message(
                config.ADMIN_CHAT_ID,
                f"❌ *Ошибка при отправке поста {processed_post_id}*\n\n"
                f"Причина: {str(e)}",
                parse_mode="Markdown"
            )
        except:
            pass


async def _prepare_media_group(image_urls: List[str]) -> List[InputMediaPhoto]:
    """
    Подготавливает медиа-группу из изображений.
    
    Args:
        image_urls: Список URL или base64 изображений
    
    Returns:
        Список InputMediaPhoto для отправки
    """
    media_group = []
    
    for idx, image_data in enumerate(image_urls[:10]):  # Telegram лимит: 10 изображений
        try:
            if image_data.startswith("data:image"):
                # Base64 изображение
                img_base64 = image_data.split(",")[1]
                img_bytes = base64.b64decode(img_base64)
                
                # Создаем InputFile из байтов
                input_file = BufferedInputFile(
                    file=img_bytes,
                    filename=f"slide_{idx + 1}.png"
                )
                
                media_group.append(InputMediaPhoto(media=input_file))
                
            elif image_data.startswith("http"):
                # URL изображения (может быть с Яндекс.Диска)
                media_group.append(InputMediaPhoto(media=image_data))
            
            else:
                logger.warning(f"Unknown image format: {image_data[:50]}")
                
        except Exception as e:
            logger.error(f"Error preparing image {idx + 1}: {e}")
            continue
    
    logger.info(f"Prepared {len(media_group)} images for media group")
    return media_group


def _format_approval_message(
    original_post: OriginalPost,
    processed_post: ProcessedPost
) -> str:
    """
    Форматирует текст сообщения для одобрения.
    
    Args:
        original_post: Оригинальный пост
        processed_post: Обработанный пост
    
    Returns:
        Отформатированный текст
    """
    # Эмодзи для статистики
    likes_emoji = "🔥" if original_post.likes >= 10000 else "❤️"
    
    text = f"""
📊 *НОВЫЙ ПОСТ НА ПРОВЕРКУ*

*Источник:*
👤 Author: @{original_post.author}
{likes_emoji} Likes: {original_post.likes:,}
💬 Comments: {original_post.comments:,}
🔗 [Оригинал]({original_post.post_url})

━━━━━━━━━━━━━━━━━━━━

*📝 Новый контент:*

*{processed_post.title}*

{processed_post.caption}

{processed_post.hashtags}

━━━━━━━━━━━━━━━━━━━━

*📊 Метрики:*
🤖 AI Model: {processed_post.ai_model}
🔢 Tokens: {processed_post.tokens_used:,}
💰 Cost: ${processed_post.cost_usd:.4f}
🖼 Slides: {processed_post.slides_count}

*Выберите действие:*
"""
    
    return text.strip()


# ==================== CALLBACK HANDLERS ====================

@router.callback_query(F.data.startswith("approve:"))
async def callback_approve(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "✅ Одобрить".
    
    Шаги:
    1. Извлечь post_id из callback.data
    2. Обновить статус в БД (APPROVED)
    3. Сохранить в ApprovalHistory
    4. Отправить подтверждение
    """
    await callback.answer()
    
    # Извлекаем ID поста
    post_id = int(callback.data.split(":")[1])
    
    logger.info(f"User {callback.from_user.id} approving post {post_id}")
    
    try:
        async for session in get_session():
            # Получаем пост
            result = await session.execute(
                select(ProcessedPost).where(ProcessedPost.id == post_id)
            )
            post = result.scalar_one_or_none()
            
            if not post:
                await callback.message.edit_text("❌ Пост не найден")
                return
            
            # Обновляем статус
            post.status = ProcessedStatus.APPROVED
            session.add(post)
            
            # Сохраняем историю одобрения
            approval = ApprovalHistory(
                processed_post_id=post_id,
                user_id=callback.from_user.id,
                username=callback.from_user.username,
                decision=DecisionType.APPROVED,
                comment=None,
                timestamp=datetime.utcnow()
            )
            session.add(approval)
            
            await session.commit()
        
        # Обновляем сообщение
        await callback.message.edit_text(
            f"✅ *Пост одобрен!*\n\n"
            f"ID: {post_id}\n"
            f"Статус: APPROVED\n"
            f"Одобрил: @{callback.from_user.username}\n\n"
            f"Пост готов к публикации.",
            parse_mode="Markdown"
        )
        
        logger.info(f"Post {post_id} approved by {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error approving post {post_id}: {e}")
        await callback.message.answer("❌ Ошибка при одобрении поста")


@router.callback_query(F.data.startswith("reject:"))
async def callback_reject(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "❌ Отклонить".
    """
    await callback.answer()
    
    post_id = int(callback.data.split(":")[1])
    
    logger.info(f"User {callback.from_user.id} rejecting post {post_id}")
    
    try:
        async for session in get_session():
            result = await session.execute(
                select(ProcessedPost).where(ProcessedPost.id == post_id)
            )
            post = result.scalar_one_or_none()
            
            if not post:
                await callback.message.edit_text("❌ Пост не найден")
                return
            
            # Обновляем статус
            post.status = ProcessedStatus.REJECTED
            session.add(post)
            
            # Сохраняем историю
            approval = ApprovalHistory(
                processed_post_id=post_id,
                user_id=callback.from_user.id,
                username=callback.from_user.username,
                decision=DecisionType.REJECTED,
                comment=None,
                timestamp=datetime.utcnow()
            )
            session.add(approval)
            
            await session.commit()
        
        await callback.message.edit_text(
            f"❌ *Пост отклонен*\n\n"
            f"ID: {post_id}\n"
            f"Статус: REJECTED\n"
            f"Отклонил: @{callback.from_user.username}",
            parse_mode="Markdown"
        )
        
        logger.info(f"Post {post_id} rejected by {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error rejecting post {post_id}: {e}")
        await callback.message.answer("❌ Ошибка при отклонении поста")


@router.callback_query(F.data.startswith("edit_caption:"))
async def callback_edit_caption(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс редактирования caption."""
    await callback.answer()
    
    post_id = int(callback.data.split(":")[1])
    
    await state.update_data(editing_post_id=post_id)
    await state.set_state(ApprovalStates.editing_caption)
    
    await callback.message.answer(
        "✏️ *Редактирование текста*\n\n"
        "Отправьте новый текст для поста.\n"
        "Для отмены отправьте /cancel",
        parse_mode="Markdown"
    )


@router.message(ApprovalStates.editing_caption)
async def process_caption_edit(message: Message, state: FSMContext):
    """Обрабатывает новый caption."""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Редактирование отменено")
        return
    
    data = await state.get_data()
    post_id = data.get("editing_post_id")
    
    new_caption = message.text
    
    try:
        async for session in get_session():
            result = await session.execute(
                select(ProcessedPost).where(ProcessedPost.id == post_id)
            )
            post = result.scalar_one_or_none()
            
            if post:
                post.caption = new_caption
                session.add(post)
                await session.commit()
        
        await message.answer(
            f"✅ *Текст обновлен!*\n\n"
            f"Новый текст:\n{new_caption[:200]}...",
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error updating caption: {e}")
        await message.answer("❌ Ошибка при обновлении текста")


@router.callback_query(F.data.startswith("edit_hashtags:"))
async def callback_edit_hashtags(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс редактирования хештегов."""
    await callback.answer()
    
    post_id = int(callback.data.split(":")[1])
    
    await state.update_data(editing_post_id=post_id)
    await state.set_state(ApprovalStates.editing_hashtags)
    
    await callback.message.answer(
        "🏷 *Редактирование хештегов*\n\n"
        "Отправьте новые хештеги (через пробел).\n"
        "Пример: #бизнес #мотивация #успех\n\n"
        "Для отмены отправьте /cancel",
        parse_mode="Markdown"
    )


@router.message(ApprovalStates.editing_hashtags)
async def process_hashtags_edit(message: Message, state: FSMContext):
    """Обрабатывает новые хештеги."""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Редактирование отменено")
        return
    
    data = await state.get_data()
    post_id = data.get("editing_post_id")
    
    new_hashtags = message.text
    
    try:
        async for session in get_session():
            result = await session.execute(
                select(ProcessedPost).where(ProcessedPost.id == post_id)
            )
            post = result.scalar_one_or_none()
            
            if post:
                post.hashtags = new_hashtags
                session.add(post)
                await session.commit()
        
        await message.answer(
            f"✅ *Хештеги обновлены!*\n\n"
            f"Новые хештеги:\n{new_hashtags}",
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error updating hashtags: {e}")
        await message.answer("❌ Ошибка при обновлении хештегов")
