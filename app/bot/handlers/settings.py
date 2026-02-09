"""
Обработчики настроек и управления авторами Instagram.
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.config import get_config
from app.models import get_session, AuthorSettings
from app.models.post import OriginalPost
from app.models.processed_post import ProcessedPost, ProcessedStatus
from app.services.author_manager import (
    AuthorManager,
    MIN_LIKES_LOWER,
    MAX_AGE_DAYS_MIN,
    MAX_AGE_DAYS_MAX,
)
from app.bot.keyboards.inline_keyboards import get_main_menu
from app.bot.keyboards.settings import (
    settings_menu,
    authors_list,
    author_actions,
    edit_author_menu,
    back_to_authors,
)
from app.bot.states import AddAuthorStates, EditAuthorStates
from sqlalchemy import select, func

router = Router(name="settings")
config = get_config()


def _format_author(a: AuthorSettings) -> str:
    """Форматирует блок про одного автора."""
    status = "✅ Активен" if a.is_active else "⏸ Неактивен"
    return (
        f"👤 Автор: @{a.username}\n"
        f"💗 Минимум лайков: {a.min_likes:,}\n"
        f"📅 Возраст постов: {a.max_post_age_days} дн.\n"
        f"{status}\n"
    )


# ---------- /settings ----------


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Настройки: общая статистика + кнопка «Управление авторами»."""
    if message.from_user and message.from_user.id != config.ADMIN_CHAT_ID:
        await message.answer("❌ У вас нет доступа к этому боту.")
        return

    try:
        authors = await AuthorManager.get_all_authors(message.from_user.id)
        active = [a for a in authors if a.is_active]
        total_authors = len(authors)
        active_count = len(active)

        async with get_session() as session:
            pending_result = await session.execute(
                select(func.count(ProcessedPost.id)).where(
                    ProcessedPost.status == ProcessedStatus.PENDING_APPROVAL
                )
            )
            pending = pending_result.scalar() or 0
            total_posts_result = await session.execute(
                select(func.count(OriginalPost.id))
            )
            total_posts = total_posts_result.scalar() or 0

        text = (
            "⚙️ <b>Настройки</b>\n\n"
            "📊 <b>Статистика:</b>\n"
            f"👥 Всего авторов: {total_authors}\n"
            f"✅ Активных: {active_count}\n"
            f"📝 Всего постов в базе: {total_posts}\n"
            f"⏳ На одобрении: {pending}\n\n"
            "Выберите действие:"
        )
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=settings_menu(),
        )
        logger.info(f"User {message.from_user.id} opened settings")
    except Exception as e:
        logger.exception(f"Error in /settings: {e}")
        await message.answer(
            "❌ Не удалось загрузить настройки. Попробуйте позже.",
            reply_markup=get_main_menu(),
        )


@router.callback_query(F.data == "settings_open")
async def callback_settings_open(callback: CallbackQuery):
    """Открытие настроек из кнопки меню."""
    await callback.answer()
    if callback.from_user and callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    if not callback.message:
        return

    try:
        authors = await AuthorManager.get_all_authors(callback.from_user.id)
        active = [a for a in authors if a.is_active]
        total_authors = len(authors)
        active_count = len(active)

        async with get_session() as session:
            pending_result = await session.execute(
                select(func.count(ProcessedPost.id)).where(
                    ProcessedPost.status == ProcessedStatus.PENDING_APPROVAL
                )
            )
            pending = pending_result.scalar() or 0
            total_posts_result = await session.execute(
                select(func.count(OriginalPost.id))
            )
            total_posts = total_posts_result.scalar() or 0

        text = (
            "⚙️ <b>Настройки</b>\n\n"
            "📊 <b>Статистика:</b>\n"
            f"👥 Всего авторов: {total_authors}\n"
            f"✅ Активных: {active_count}\n"
            f"📝 Всего постов в базе: {total_posts}\n"
            f"⏳ На одобрении: {pending}\n\n"
            "Выберите действие:"
        )
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=settings_menu(),
        )
    except Exception as e:
        logger.exception(f"Error opening settings: {e}")
        await callback.message.edit_text(
            "❌ Не удалось загрузить настройки.",
            reply_markup=get_main_menu(),
        )


# ---------- /authors и список авторов ----------


@router.message(Command("authors"))
async def cmd_authors(message: Message):
    """Список всех авторов с настройками и кнопками."""
    if message.from_user and message.from_user.id != config.ADMIN_CHAT_ID:
        return

    await _reply_authors_list(message.answer, message.from_user.id)


@router.callback_query(F.data == "settings_authors")
async def callback_settings_authors(callback: CallbackQuery, state: FSMContext):
    """Переход к списку авторов из настроек."""
    await callback.answer()
    await state.clear()
    if callback.from_user and callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    if not callback.message:
        return

    async def reply(text: str, **kwargs):
        await callback.message.edit_text(text, **kwargs)

    await _reply_authors_list(reply, callback.from_user.id)


async def _reply_authors_list(send_fn, admin_telegram_id: int, **kwargs):
    """Формирует и отправляет список авторов с клавиатурой. send_fn(text, **kwargs) — async."""
    try:
        authors = await AuthorManager.get_all_authors(admin_telegram_id)
        count = len(authors) if authors is not None else 0
        logger.info(
            "authors_list: admin_telegram_id=%s, authors_count=%s",
            admin_telegram_id,
            count,
        )

        if not authors or count == 0:
            text = (
                "📋 <b>Управление авторами</b>\n\n"
                "У вас пока нет отслеживаемых авторов. Добавьте первого через /add_author"
            )
            await send_fn(
                text,
                parse_mode="HTML",
                reply_markup=authors_list([]),
                **kwargs,
            )
            return

        if not isinstance(authors, list):
            logger.warning(
                "authors_list: authors is not a list, type=%s",
                type(authors).__name__,
            )
            authors = list(authors) if authors else []

        valid_authors = [a for a in authors if isinstance(a, AuthorSettings)]
        if len(valid_authors) != len(authors):
            logger.warning(
                "authors_list: filtered to AuthorSettings only, was %s, now %s",
                len(authors),
                len(valid_authors),
            )
            authors = valid_authors

        blocks = ["📋 <b>Управление авторами</b>\n"]
        for a in authors:
            blocks.append(_format_author(a))
        text = "\n".join(blocks)
        await send_fn(
            text,
            parse_mode="HTML",
            reply_markup=authors_list(authors),
            **kwargs,
        )
    except Exception as e:
        logger.exception("Error listing authors: admin_telegram_id=%s, error=%s", admin_telegram_id, e)
        await send_fn(
            "❌ Не удалось загрузить список авторов.",
            reply_markup=get_main_menu(),
            **kwargs,
        )


# ---------- Добавление автора (FSM) ----------


@router.message(Command("add_author"))
async def cmd_add_author(message: Message, state: FSMContext):
    """Начать добавление автора."""
    if message.from_user and message.from_user.id != config.ADMIN_CHAT_ID:
        return
    await state.set_state(AddAuthorStates.username)
    await message.answer(
        "➕ <b>Добавление автора</b>\n\n"
        "Введите Instagram username (без @):",
        parse_mode="HTML",
        reply_markup=back_to_authors(),
    )
    logger.info(f"User {message.from_user.id} started add_author")


@router.callback_query(F.data == "author_add")
async def callback_author_add(callback: CallbackQuery, state: FSMContext):
    """Кнопка «Добавить автора»."""
    await callback.answer()
    if callback.from_user and callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    if not callback.message:
        return
    await state.set_state(AddAuthorStates.username)
    await callback.message.edit_text(
        "➕ <b>Добавление автора</b>\n\n"
        "Введите Instagram username (без @):",
        parse_mode="HTML",
        reply_markup=back_to_authors(),
    )


@router.message(AddAuthorStates.username, F.text)
async def add_author_username(message: Message, state: FSMContext):
    username = (message.text or "").strip().replace("@", "")
    if not username:
        await message.answer("❌ Введите непустой username.")
        return
    username = username.lower()
    await state.update_data(username=username)
    await state.set_state(AddAuthorStates.min_likes)
    await message.answer(
        f"💗 Введите <b>минимум лайков</b> для постов (число, не меньше {MIN_LIKES_LOWER}):\n\n"
        "Или отправьте 0 для значения по умолчанию (1 000).",
        parse_mode="HTML",
        reply_markup=back_to_authors(),
    )


@router.message(AddAuthorStates.min_likes, F.text)
async def add_author_min_likes(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == "0":
        min_likes = 1000
    else:
        try:
            min_likes = int(text)
        except ValueError:
            await message.answer("❌ Введите число (например 1000 или 0 для 1000).")
            return
        if min_likes < MIN_LIKES_LOWER:
            await message.answer(f"❌ Минимум лайков не может быть меньше {MIN_LIKES_LOWER}.")
            return
    await state.update_data(min_likes=min_likes)
    await state.set_state(AddAuthorStates.max_age_days)
    await message.answer(
        f"📅 Введите <b>максимальный возраст поста</b> в днях (от {MAX_AGE_DAYS_MIN} до {MAX_AGE_DAYS_MAX}):\n\n"
        "Или отправьте 0 для значения по умолчанию (3).",
        parse_mode="HTML",
        reply_markup=back_to_authors(),
    )


@router.message(AddAuthorStates.max_age_days, F.text)
async def add_author_max_age(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == "0":
        max_age_days = 3
    else:
        try:
            max_age_days = int(text)
        except ValueError:
            await message.answer("❌ Введите число (например 3 или 0 для 3).")
            return
        if not (MAX_AGE_DAYS_MIN <= max_age_days <= MAX_AGE_DAYS_MAX):
            await message.answer(
                f"❌ Возраст постов должен быть от {MAX_AGE_DAYS_MIN} до {MAX_AGE_DAYS_MAX} дней."
            )
            return
    await state.update_data(max_age_days=max_age_days)
    await state.set_state(AddAuthorStates.confirm)
    data = await state.get_data()
    username = data.get("username", "")
    min_likes = data.get("min_likes", 1000)
    summary = (
        "✅ <b>Проверьте данные:</b>\n\n"
        f"👤 Автор: @{username}\n"
        f"💗 Минимум лайков: {min_likes:,}\n"
        f"📅 Возраст постов: {max_age_days} дн.\n\n"
        "Подтвердить добавление?"
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="add_author_confirm"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="add_author_cancel"),
    )
    builder.row(
        InlineKeyboardButton(text="📋 К списку авторов", callback_data="settings_authors"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"),
    )
    await message.answer(
        summary,
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "add_author_confirm")
async def add_author_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.from_user and callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    if not callback.message:
        return

    data = await state.get_data()
    await state.clear()
    username = data.get("username", "")
    min_likes = data.get("min_likes", 1000)
    max_age_days = data.get("max_age_days", 3)

    try:
        await AuthorManager.add_author(
            username=username,
            admin_telegram_id=callback.from_user.id,
            admin_username=callback.from_user.username,
            min_likes=min_likes,
            max_age_days=max_age_days,
        )
        await callback.message.edit_text(
            f"✅ Автор @{username} успешно добавлен!\n\n"
            f"💗 Минимум лайков: {min_likes:,}\n"
            f"📅 Возраст постов: {max_age_days} дн.",
            parse_mode="HTML",
            reply_markup=back_to_authors(),
        )
        logger.info(f"Author @{username} added by user {callback.from_user.id}")
    except ValueError as e:
        await callback.message.edit_text(
            f"❌ {str(e)}",
            reply_markup=back_to_authors(),
        )
    except Exception as e:
        logger.exception(f"Error adding author: {e}")
        await callback.message.edit_text(
            "❌ Не удалось добавить автора. Попробуйте позже.",
            reply_markup=back_to_authors(),
        )


@router.callback_query(F.data == "add_author_cancel")
async def add_author_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    if callback.from_user and callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    if not callback.message:
        return
    await callback.message.edit_text(
        "❌ Добавление отменено.",
        reply_markup=back_to_authors(),
    )


@router.callback_query(F.data == "settings_authors", AddAuthorStates)
async def add_author_cancel_via_list(callback: CallbackQuery, state: FSMContext):
    """Выход из FSM добавления по кнопке «К списку авторов»."""
    await state.clear()
    await callback.answer()
    if callback.from_user and callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    if not callback.message:
        return
    await _reply_authors_list(
        lambda t, **kw: callback.message.edit_text(t, **kw),
        callback.from_user.id,
    )


# ---------- Редактирование автора ----------


@router.callback_query(F.data.startswith("author_edit:"))
async def callback_author_edit(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user and callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    if not callback.message:
        return

    username = callback.data.replace("author_edit:", "", 1)
    author = await AuthorManager.get_author(username)
    if not author:
        await callback.message.edit_text(
            f"❌ Автор @{username} не найден.",
            reply_markup=back_to_authors(),
        )
        return
    text = "✏️ <b>Редактирование автора</b>\n\n" + _format_author(author)
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=edit_author_menu(username),
    )


@router.callback_query(F.data.startswith("edit_author_field:"))
async def callback_edit_author_field(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.from_user and callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    if not callback.message:
        return

    parts = callback.data.replace("edit_author_field:", "", 1).split(":", 1)
    username = parts[0]
    field = parts[1] if len(parts) > 1 else ""

    if field == "is_active":
        author = await AuthorManager.get_author(username)
        if not author:
            await callback.message.edit_text("❌ Автор не найден.", reply_markup=back_to_authors())
            return
        new_active = not author.is_active
        await AuthorManager.update_author(username, is_active=new_active)
        status = "активен" if new_active else "неактивен"
        await callback.message.edit_text(
            f"✅ Автор @{username} теперь {status}.",
            parse_mode="HTML",
            reply_markup=edit_author_menu(username),
        )
        return

    await state.update_data(edit_author_username=username, edit_author_field=field)
    await state.set_state(EditAuthorStates.new_value)
    if field == "min_likes":
        prompt = f"💗 Введите новое значение <b>минимум лайков</b> (не меньше {MIN_LIKES_LOWER}):"
    elif field == "max_age_days":
        prompt = f"📅 Введите новый <b>возраст постов</b> в днях (от {MAX_AGE_DAYS_MIN} до {MAX_AGE_DAYS_MAX}):"
    else:
        await state.clear()
        return
    await callback.message.edit_text(
        prompt,
        parse_mode="HTML",
        reply_markup=back_to_authors(),
    )


@router.message(EditAuthorStates.new_value, F.text)
async def edit_author_new_value(message: Message, state: FSMContext):
    data = await state.get_data()
    username = data.get("edit_author_username", "")
    field = data.get("edit_author_field", "")
    text = (message.text or "").strip()

    try:
        if field == "min_likes":
            val = int(text)
            if val < MIN_LIKES_LOWER:
                await message.answer(f"❌ Минимум лайков не может быть меньше {MIN_LIKES_LOWER}.")
                return
            await AuthorManager.update_author(username, min_likes=val)
            await message.answer(
                f"✅ Минимум лайков для @{username} установлен: {val:,}",
                parse_mode="HTML",
                reply_markup=edit_author_menu(username),
            )
        elif field == "max_age_days":
            val = int(text)
            if not (MAX_AGE_DAYS_MIN <= val <= MAX_AGE_DAYS_MAX):
                await message.answer(
                    f"❌ Возраст постов должен быть от {MAX_AGE_DAYS_MIN} до {MAX_AGE_DAYS_MAX}."
                )
                return
            await AuthorManager.update_author(username, max_age_days=val)
            await message.answer(
                f"✅ Возраст постов для @{username}: {val} дн.",
                parse_mode="HTML",
                reply_markup=edit_author_menu(username),
            )
        else:
            await message.answer("❌ Неизвестное поле.", reply_markup=back_to_authors())
    except ValueError:
        await message.answer("❌ Введите корректное число.", reply_markup=back_to_authors())
        return
    await state.clear()


# ---------- Удаление автора ----------


@router.callback_query(F.data.startswith("author_delete:"))
async def callback_author_delete(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user and callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    if not callback.message:
        return

    username = callback.data.replace("author_delete:", "", 1)
    removed = await AuthorManager.remove_author(username)
    if removed:
        await callback.message.edit_text(
            f"🗑 Автор @{username} удалён из списка.",
            parse_mode="HTML",
            reply_markup=back_to_authors(),
        )
        logger.info(f"Author @{username} removed by user {callback.from_user.id}")
    else:
        await callback.message.edit_text(
            f"❌ Автор @{username} не найден.",
            reply_markup=back_to_authors(),
        )
