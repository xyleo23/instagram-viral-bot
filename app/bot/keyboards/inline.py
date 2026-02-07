from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_approval_keyboard(processed_post_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для одобрения/отклонения поста.
    
    Args:
        processed_post_id: ID обработанного поста
    
    Returns:
        Inline клавиатура с кнопками
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=f"approve:{processed_post_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"reject:{processed_post_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Редактировать текст",
            callback_data=f"edit_caption:{processed_post_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🏷 Изменить хештеги",
            callback_data=f"edit_hashtags:{processed_post_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔗 Открыть на Яндекс.Диске",
            url="PLACEHOLDER_URL"  # Будет заменено в runtime
        )
    )
    
    return builder.as_markup()


def get_queue_navigation_keyboard(
    page: int,
    total_pages: int
) -> InlineKeyboardMarkup:
    """
    Клавиатура для навигации по очереди постов.
    
    Args:
        page: Текущая страница
        total_pages: Всего страниц
    
    Returns:
        Inline клавиатура
    """
    builder = InlineKeyboardBuilder()
    
    buttons = []
    
    if page > 0:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"queue_page:{page - 1}"
            )
        )
    
    buttons.append(
        InlineKeyboardButton(
            text=f"📄 {page + 1}/{total_pages}",
            callback_data="queue_noop"
        )
    )
    
    if page < total_pages - 1:
        buttons.append(
            InlineKeyboardButton(
                text="➡️ Вперед",
                callback_data=f"queue_page:{page + 1}"
            )
        )
    
    builder.row(*buttons)
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=f"queue_page:{page}"
        )
    )
    
    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📋 Очередь", callback_data="show_queue"),
        InlineKeyboardButton(text="📊 Статус", callback_data="show_status")
    )
    
    builder.row(
        InlineKeyboardButton(text="📜 История", callback_data="show_history")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔍 Парсить аккаунт", callback_data="parse_account")
    )
    
    return builder.as_markup()
