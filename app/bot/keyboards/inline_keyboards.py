from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню с постоянными кнопками."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📥 Очередь", callback_data="show_queue"))
    builder.row(
        InlineKeyboardButton(text="📊 Статус", callback_data="show_status"),
        InlineKeyboardButton(text="📜 История", callback_data="show_history")
    )
    builder.row(InlineKeyboardButton(text="📅 Расписание", callback_data="show_schedule"))
    builder.row(
        InlineKeyboardButton(text="🔎 Парсить аккаунт", callback_data="start_parsing"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings_open"),
    )
    return builder.as_markup()


def get_queue_keyboard_with_menu(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Клавиатура очереди с навигацией и главным меню."""
    builder = InlineKeyboardBuilder()

    # Навигация по страницам
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"queue_page:{page - 1}")
        )
    nav_buttons.append(
        InlineKeyboardButton(text=f"📄 {page + 1}/{total_pages}", callback_data="queue_noop")
    )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️ Вперед", callback_data=f"queue_page:{page + 1}")
        )
    builder.row(*nav_buttons)
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"queue_page:{page}")
    )

    # Главное меню
    builder.row(InlineKeyboardButton(text="📥 Очередь", callback_data="show_queue"))
    builder.row(
        InlineKeyboardButton(text="📊 Статус", callback_data="show_status"),
        InlineKeyboardButton(text="📜 История", callback_data="show_history")
    )
    builder.row(InlineKeyboardButton(text="📅 Расписание", callback_data="show_schedule"))
    builder.row(
        InlineKeyboardButton(text="🔎 Парсить аккаунт", callback_data="start_parsing"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings_open"),
    )

    return builder.as_markup()
