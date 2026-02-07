"""
Обработчик системы одобрения постов
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.utils.logger import log

router = Router()


@router.callback_query(F.data.startswith("approve_"))
async def approve_post(callback: CallbackQuery):
    """Одобряет пост"""
    try:
        post_id = int(callback.data.split("_")[1])
        
        # TODO: Реализовать логику одобрения из БД
        await callback.answer("✅ Пост одобрен!")
        await callback.message.edit_text(
            f"✅ Пост одобрен!\n\nБудет опубликован по расписанию."
        )
        log.info(f"Пост {post_id} одобрен пользователем {callback.from_user.id}")
        
    except Exception as e:
        log.error(f"Ошибка в approve_post: {e}")
        await callback.answer("❌ Ошибка при одобрении", show_alert=True)


@router.callback_query(F.data.startswith("reject_"))
async def reject_post(callback: CallbackQuery):
    """Отклоняет пост"""
    try:
        post_id = int(callback.data.split("_")[1])
        
        # TODO: Реализовать логику отклонения из БД
        await callback.answer("❌ Пост отклонён")
        await callback.message.edit_text("❌ Пост отклонён.")
        log.info(f"Пост {post_id} отклонен пользователем {callback.from_user.id}")
        
    except Exception as e:
        log.error(f"Ошибка в reject_post: {e}")
        await callback.answer("❌ Ошибка при отклонении", show_alert=True)


def create_approval_keyboard(post_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для одобрения поста"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Одобрить",
                callback_data=f"approve_{post_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject_{post_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎨 Сгенерировать карусель",
                callback_data=f"generate_{post_id}"
            )
        ]
    ])
