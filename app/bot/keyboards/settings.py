"""
Клавиатуры для раздела настроек и управления авторами.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.author_settings import AuthorSettings


def settings_menu() -> InlineKeyboardMarkup:
    """Главное меню настроек."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⚙️ Управление авторами",
            callback_data="settings_authors",
        )
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()


def authors_list(authors: list[AuthorSettings]) -> InlineKeyboardMarkup:
    """Список авторов с кнопками [✏️ Изменить] [🗑️ Удалить] для каждого."""
    builder = InlineKeyboardBuilder()
    for author in authors:
        builder.row(
            InlineKeyboardButton(
                text=f"✏️ Изменить",
                callback_data=f"author_edit:{author.username}",
            ),
            InlineKeyboardButton(
                text=f"🗑️ Удалить",
                callback_data=f"author_delete:{author.username}",
            ),
        )
    builder.row(
        InlineKeyboardButton(text="➕ Добавить автора", callback_data="author_add"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="settings_authors"),
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()


def author_actions(username: str) -> InlineKeyboardMarkup:
    """Действия над автором: изменить, удалить."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить",
            callback_data=f"author_edit:{username}",
        ),
        InlineKeyboardButton(
            text="🗑️ Удалить",
            callback_data=f"author_delete:{username}",
        ),
    )
    builder.row(
        InlineKeyboardButton(text="📋 К списку авторов", callback_data="settings_authors"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"),
    )
    return builder.as_markup()


def edit_author_menu(username: str) -> InlineKeyboardMarkup:
    """Меню редактирования автора: какие поля менять."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💗 Минимум лайков",
            callback_data=f"edit_author_field:{username}:min_likes",
        ),
        InlineKeyboardButton(
            text="📅 Возраст постов (дни)",
            callback_data=f"edit_author_field:{username}:max_age_days",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="✅/⏸ Активность",
            callback_data=f"edit_author_field:{username}:is_active",
        ),
    )
    builder.row(
        InlineKeyboardButton(text="📋 К списку авторов", callback_data="settings_authors"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"),
    )
    return builder.as_markup()


def confirm_cancel_keyboard(callback_prefix: str) -> InlineKeyboardMarkup:
    """Кнопки Подтвердить / Отмена для FSM."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"{callback_prefix}_confirm"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"{callback_prefix}_cancel"),
    )
    return builder.as_markup()


def back_to_authors() -> InlineKeyboardMarkup:
    """Назад к списку авторов."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 К списку авторов", callback_data="settings_authors"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"),
    )
    return builder.as_markup()
