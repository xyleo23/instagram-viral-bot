"""
Модуль планирования публикаций в Telegram боте.

Обработчики для:
- Просмотр календаря запланированных постов
- Планирование публикации (дата/время)
- Список запланированных постов
- Отмена запланированной публикации
"""
import calendar
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from loguru import logger

from app.config import get_config
from app.models import (
    get_session,
    ProcessedPost,
    OriginalPost,
    ProcessedStatus,
)
from app.bot.keyboards.inline_keyboards import get_main_menu
from sqlalchemy import select, and_

router = Router(name="schedule")
config = get_config()

MOSCOW_TZ = ZoneInfo("Europe/Moscow")

def format_datetime_moscow(dt: datetime) -> str:
    """Форматирует дату/время в московском часовом поясе: ДД.ММ.ГГГГ в ЧЧ:ММ"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(MOSCOW_TZ)
    else:
        dt = dt.astimezone(MOSCOW_TZ)
    return dt.strftime("%d.%m.%Y в %H:%M")


# ==================== KEYBOARDS ====================


def get_schedule_menu_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура меню расписания."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Список запланированных", callback_data="list_scheduled_posts")
    )
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder


def get_calendar_keyboard(year: int, month: int, post_id: int) -> InlineKeyboardBuilder:
    """Inline календарь для выбора даты."""
    builder = InlineKeyboardBuilder()
    
    # Заголовок: месяц год
    month_names = [
        "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    
    # Навигация по месяцам
    builder.row(
        InlineKeyboardButton(text="◀️", callback_data=f"cal_prev:{post_id}:{year}:{month}"),
        InlineKeyboardButton(text=f"{month_names[month]} {year}", callback_data="cal_noop"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal_next:{post_id}:{year}:{month}")
    )
    
    # Дни недели
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    builder.row(*[InlineKeyboardButton(text=wd, callback_data="cal_noop") for wd in weekdays])
    
    # Дни месяца
    cal = calendar.Calendar(firstweekday=0)  # Понедельник
    today = datetime.now(MOSCOW_TZ).date()
    
    for week in cal.monthdayscalendar(year, month):
        row_buttons = []
        for day in week:
            if day == 0:
                row_buttons.append(InlineKeyboardButton(text=" ", callback_data="cal_noop"))
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                btn_text = str(day)
                row_buttons.append(
                    InlineKeyboardButton(
                        text=btn_text,
                        callback_data=f"cal_date:{post_id}:{date_str}"
                    )
                )
        builder.row(*row_buttons)
    
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data=f"schedule_cancel:{post_id}"))
    return builder


def get_time_keyboard(post_id: int, date_str: str) -> InlineKeyboardBuilder:
    """Клавиатура выбора времени публикации (популярные слоты)."""
    builder = InlineKeyboardBuilder()
    
    # Типичные времена для Instagram: 9:00, 12:00, 15:00, 18:00, 21:00
    times = ["09:00", "12:00", "15:00", "18:00", "21:00"]
    
    row1 = [
        InlineKeyboardButton(text=t, callback_data=f"cal_time:{post_id}:{date_str}:{t}")
        for t in times[:3]
    ]
    row2 = [
        InlineKeyboardButton(text=t, callback_data=f"cal_time:{post_id}:{date_str}:{t}")
        for t in times[3:]
    ]
    builder.row(*row1)
    builder.row(*row2)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data=f"schedule_cancel:{post_id}"))
    return builder


# ==================== HANDLERS ====================


@router.callback_query(F.data == "show_schedule")
async def show_schedule_menu(callback: CallbackQuery):
    """Показать меню расписания (календарь запланированных постов)."""
    await callback.answer()
    
    if callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    try:
        async with get_session() as session:
            result = await session.execute(
                select(ProcessedPost)
                .where(
                    and_(
                        ProcessedPost.publication_status == "SCHEDULED",
                        ProcessedPost.scheduled_at.isnot(None)
                    )
                )
                .order_by(ProcessedPost.scheduled_at.asc())
            )
            scheduled_posts = result.scalars().all()
        
        if scheduled_posts:
            lines = ["📅 *Запланированные публикации:*\n"]
            for post in scheduled_posts[:10]:
                dt_str = format_datetime_moscow(post.scheduled_at) if post.scheduled_at else "—"
                lines.append(f"• ID {post.id}: {dt_str}")
            if len(scheduled_posts) > 10:
                lines.append(f"\n_...и ещё {len(scheduled_posts) - 10}_")
            text = "\n".join(lines)
        else:
            text = (
                "📅 *Расписание публикаций*\n\n"
                "Нет запланированных постов.\n\n"
                "Одобренные посты можно запланировать из очереди или "
                "после нажатия «✅ Одобрить» — появится кнопка «📅 Запланировать»."
            )
        
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_schedule_menu_keyboard().as_markup()
        )
    except Exception as e:
        logger.error(f"Error in show_schedule_menu: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке расписания",
            reply_markup=get_main_menu()
        )


@router.callback_query(F.data.startswith("schedule_post:"))
async def schedule_post(callback: CallbackQuery):
    """Начать планирование поста — показать календарь."""
    await callback.answer()
    
    if callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    post_id = int(callback.data.split(":")[1])
    
    # Проверяем, что пост одобрен
    async with get_session() as session:
        result = await session.execute(
            select(ProcessedPost).where(ProcessedPost.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            await callback.message.edit_text("❌ Пост не найден", reply_markup=get_main_menu())
            return
        if post.status != ProcessedStatus.APPROVED:
            await callback.message.edit_text(
                "❌ Можно планировать только одобренные посты.",
                reply_markup=get_main_menu()
            )
            return
    
    now = datetime.now(MOSCOW_TZ)
    keyboard = get_calendar_keyboard(now.year, now.month, post_id)
    
    await callback.message.edit_text(
        f"📅 *Планирование поста #{post_id}*\n\n"
        "Выберите дату публикации:",
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith("cal_prev:"))
@router.callback_query(F.data.startswith("cal_next:"))
async def calendar_navigate(callback: CallbackQuery):
    """Навигация по календарю (пред/след месяц)."""
    await callback.answer()
    
    if callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    parts = callback.data.split(":")
    direction = "prev" if "prev" in callback.data else "next"
    post_id = int(parts[1])
    year = int(parts[2])
    month = int(parts[3])
    
    if direction == "prev":
        if month == 1:
            year, month = year - 1, 12
        else:
            month -= 1
    else:
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    
    keyboard = get_calendar_keyboard(year, month, post_id)
    await callback.message.edit_reply_markup(reply_markup=keyboard.as_markup())


@router.callback_query(F.data.startswith("cal_date:"))
async def calendar_date_selected(callback: CallbackQuery):
    """Выбрана дата — показать выбор времени."""
    await callback.answer()
    
    if callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    parts = callback.data.split(":")
    post_id = int(parts[1])
    date_str = parts[2]
    
    keyboard = get_time_keyboard(post_id, date_str)
    
    # Парсим дату для отображения
    y, m, d = map(int, date_str.split("-"))
    date_display = f"{d:02d}.{m:02d}.{y}"
    
    await callback.message.edit_text(
        f"📅 *Пост #{post_id}*\n\n"
        f"Дата: {date_display}\n"
        "Выберите время публикации:",
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith("cal_time:"))
async def calendar_time_selected(callback: CallbackQuery):
    """Выбрано время — сохраняем в БД и подтверждаем."""
    await callback.answer()
    
    if callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    parts = callback.data.split(":")
    post_id = int(parts[1])
    date_str = parts[2]
    time_str = parts[3]  # HH:MM
    
    # Собираем datetime в московском часовом поясе
    y, m, d = map(int, date_str.split("-"))
    hour, minute = map(int, time_str.split(":"))
    dt_moscow = datetime(y, m, d, hour, minute, tzinfo=MOSCOW_TZ)
    
    try:
        async with get_session() as session:
            result = await session.execute(
                select(ProcessedPost).where(ProcessedPost.id == post_id)
            )
            post = result.scalar_one_or_none()
            if not post:
                await callback.message.edit_text("❌ Пост не найден", reply_markup=get_main_menu())
                return
            
            post.scheduled_at = dt_moscow
            post.publication_status = "SCHEDULED"
            session.add(post)
            await session.commit()
        
        dt_display = format_datetime_moscow(dt_moscow)
        await callback.message.edit_text(
            f"✅ *Публикация запланирована!*\n\n"
            f"Пост #{post_id}\n"
            f"📅 {dt_display} (МСК)",
            parse_mode="Markdown",
            reply_markup=get_schedule_menu_keyboard().as_markup()
        )
        logger.info(f"Post {post_id} scheduled for {dt_display}")
        
    except Exception as e:
        logger.error(f"Error scheduling post {post_id}: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при сохранении расписания",
            reply_markup=get_main_menu()
        )


@router.callback_query(F.data.startswith("schedule_cancel:"))
async def schedule_cancel(callback: CallbackQuery):
    """Отмена выбора даты/времени."""
    await callback.answer()
    
    if callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    await callback.message.edit_text(
        "❌ Планирование отменено",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "list_scheduled_posts")
async def list_scheduled_posts(callback: CallbackQuery):
    """Список всех запланированных постов."""
    await callback.answer()
    
    if callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    try:
        async with get_session() as session:
            result = await session.execute(
                select(ProcessedPost, OriginalPost)
                .join(OriginalPost, ProcessedPost.original_post_id == OriginalPost.id)
                .where(
                    and_(
                        ProcessedPost.publication_status == "SCHEDULED",
                        ProcessedPost.scheduled_at.isnot(None)
                    )
                )
                .order_by(ProcessedPost.scheduled_at.asc())
            )
            rows = result.all()
        
        if not rows:
            await callback.message.edit_text(
                "📋 *Запланированные посты*\n\n"
                "Список пуст.",
                parse_mode="Markdown",
                reply_markup=get_schedule_menu_keyboard().as_markup()
            )
            return
        
        lines = ["📋 *Запланированные публикации:*\n"]
        builder = InlineKeyboardBuilder()
        
        for post, orig in rows:
            dt_str = format_datetime_moscow(post.scheduled_at)
            lines.append(f"• *ID {post.id}* — {dt_str}\n  _{post.title[:40]}..._")
            builder.row(
                InlineKeyboardButton(
                    text=f"❌ Отменить #{post.id}",
                    callback_data=f"cancel_scheduled:{post.id}"
                )
            )
        
        builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
        
        await callback.message.edit_text(
            "\n\n".join(lines),
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        logger.error(f"Error in list_scheduled_posts: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке списка",
            reply_markup=get_main_menu()
        )


@router.callback_query(F.data.startswith("cancel_scheduled:"))
async def cancel_scheduled_post(callback: CallbackQuery):
    """Отменить запланированную публикацию."""
    await callback.answer()
    
    if callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    post_id = int(callback.data.split(":")[1])
    
    try:
        async with get_session() as session:
            result = await session.execute(
                select(ProcessedPost).where(ProcessedPost.id == post_id)
            )
            post = result.scalar_one_or_none()
            if not post:
                await callback.message.edit_text("❌ Пост не найден", reply_markup=get_main_menu())
                return
            
            post.scheduled_at = None
            post.publication_status = "NOT_SCHEDULED"
            session.add(post)
            await session.commit()
        
        await callback.answer("✅ Публикация отменена", show_alert=True)
        await callback.message.edit_text(
            f"✅ Публикация поста #{post_id} отменена.",
            reply_markup=get_schedule_menu_keyboard().as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error canceling scheduled post {post_id}: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при отмене",
            reply_markup=get_main_menu()
        )


# noop для календаря (пустые кнопки)
@router.callback_query(F.data == "cal_noop")
async def cal_noop(callback: CallbackQuery):
    await callback.answer()
