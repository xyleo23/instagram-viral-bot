"""
Модуль главного меню бота.

Централизованный обработчик кнопки "Главное меню" и отображение
главного меню с кнопками: Очередь, Статус, История, Расписание, Парсить.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.config import get_config
from app.bot.keyboards.inline_keyboards import get_main_menu

router = Router(name="menu")
config = get_config()


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Возврат в главное меню (обработчик для schedule и других модулей)."""
    await callback.answer()
    if callback.from_user and callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    if not callback.message:
        return

    text = (
        "🎉 *Instagram Viral Bot*\n\n"
        "Выберите действие:"
    )
    try:
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    except Exception:
        pass
